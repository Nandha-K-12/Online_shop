from django.urls import path

from . import views


app_name = 'payment'


urlpatterns = [
    path(
        'process/',
        views.payment_process,
        name='process',
    ),
    path(
        '',
        views.payment_process,
        name='payment_process',
    ),
    path(
        'create/',
        views.payment_create,
        name='payment_create',
    ),
    path(
        'done/',
        views.payment_done,
        name='done',
    ),
    path(
        'canceled/',
        views.payment_canceled,
        name='canceled',
    ),
]