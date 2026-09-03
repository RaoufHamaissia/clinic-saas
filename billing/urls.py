from django.urls import path
from . import views


app_name = "billing"

urlpatterns = [
    path("", views.subscription_status, name="status"),
    path("invoices/<int:pk>/pay/", views.pay_invoice, name="pay_invoice"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-failure/", views.payment_failure, name="payment_failure"),
    path("webhook/", views.chargily_webhook, name="webhook"),
]