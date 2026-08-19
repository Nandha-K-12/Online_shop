from io import BytesIO

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from orders.models import Order


@shared_task
def payment_completed(order_id):
    """
    Task to send an e-mail notification with PDF invoice when an order is
    successfully paid.
    """
    order = Order.objects.get(id=order_id)

    # create invoice e-mail
    subject = f'My Shop - Invoice no. {order.id}'
    message = 'Please find attached the invoice for your recent purchase.'
    email = EmailMessage(
        subject,
        message,
        'admin@myshop.com',
        [order.email]
    )

    # generate PDF
    html = render_to_string('orders/order/pdf.html', {'order': order})
    out = BytesIO()

    css_path = str(settings.STATIC_ROOT / 'css' / 'pdf.css')
    try:
        import weasyprint
        stylesheets = [weasyprint.CSS(css_path)]
        weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)
    except (ImportError, OSError):
        from xhtml2pdf import pisa
        pisa.CreatePDF(html, dest=out)

    # attach PDF file
    email.attach(
        f'order_{order.id}.pdf',
        out.getvalue(),
        'application/pdf'
    )

    # send e-mail
    email.send()
