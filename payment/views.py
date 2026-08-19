from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from orders.models import Order
from .braintree_gateway import gateway
from .tasks import payment_completed


def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    client_token = gateway.client_token.generate()

    return render(
        request,
        'payment/process.html',
        {
            'order': order,
            'client_token': client_token,
        }
    )


@require_POST
def payment_create(request):
    nonce = request.POST.get('payment_method_nonce')

    if not nonce:
        return JsonResponse({
            'success': False,
            'error': 'Payment nonce is missing.'
        })

    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    total_cost = order.get_total_cost() if order else Decimal('10.00')

    result = gateway.transaction.sale({
        'amount': f'{total_cost:.2f}',
        'payment_method_nonce': nonce,
        'options': {
            'submit_for_settlement': True,
        }
    })

    if result.is_success:
        if order:
            order.paid = True
            order.braintree_id = result.transaction.id
            order.save()
            # Launch asynchronous task to generate and email PDF invoice
            payment_completed.delay(order.id)

        return JsonResponse({
            'success': True,
            'transaction_id': result.transaction.id,
            'status': result.transaction.status,
        })

    return JsonResponse({
        'success': False,
        'error': result.message,
    })


def payment_done(request):
    return render(request, 'payment/done.html')


def payment_canceled(request):
    return render(request, 'payment/canceled.html')