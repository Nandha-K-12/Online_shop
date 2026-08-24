import logging
import redis
from django.conf import settings
from .models import Product

logger = logging.getLogger(__name__)

# Connect to Redis
r = redis.Redis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=getattr(settings, 'REDIS_DB', 1),
    socket_timeout=1,
    socket_connect_timeout=1
)


class Recommender:

    def get_product_key(self, id):
        return f'product:{id}:purchased_with'

    def products_bought(self, products):
        try:
            product_ids = [p.id for p in products]
            for product_id in product_ids:
                for with_id in product_ids:
                    # get the other products bought with each product
                    if product_id != with_id:
                        # increment score for product purchased together
                        r.zincrby(
                            self.get_product_key(product_id),
                            1,
                            with_id
                        )
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis error in products_bought: {e}")

    def suggest_products_for(self, products, max_results=6):
        try:
            product_ids = [p.id for p in products]
            if len(products) == 1:
                # only 1 product
                suggestions = r.zrange(
                    self.get_product_key(product_ids[0]),
                    0,
                    -1,
                    desc=True
                )[:max_results]
            else:
                # generate a temporary key
                flat_ids = ''.join([str(id) for id in product_ids])
                tmp_key = f'tmp_{flat_ids}'
                # multiple products, combine scores of all products
                # store the resulting sorted set in a temporary key
                keys = [self.get_product_key(id) for id in product_ids]
                r.zunionstore(tmp_key, keys)
                # remove ids for the products the recommendation is for
                r.zrem(tmp_key, *product_ids)
                # get the product ids by their score, descendant sort
                suggestions = r.zrange(
                    tmp_key,
                    0,
                    -1,
                    desc=True
                )[:max_results]
                # remove the temporary key
                r.delete(tmp_key)

            suggested_products_ids = [int(id) for id in suggestions]
            # get suggested products and sort by order of appearance
            suggested_products = list(
                Product.objects.filter(id__in=suggested_products_ids)
            )
            suggested_products.sort(
                key=lambda x: suggested_products_ids.index(x.id)
            )
            return suggested_products
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis error in suggest_products_for: {e}")
            return []

    def clear_purchases(self):
        try:
            for id in Product.objects.values_list('id', flat=True):
                r.delete(self.get_product_key(id))
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis error in clear_purchases: {e}")
