from django.urls import path
from .views import StartPaymentAPIView, paymob_webhook, PaymentStatusAPIView, PaymentRefreshAPIView

urlpatterns = [
    path("start/", StartPaymentAPIView.as_view()),
    path("paymob/webhook/", paymob_webhook),
    path("<int:payment_id>/status", PaymentStatusAPIView.as_view()),
    path("<int:payment_id>/refresh", PaymentRefreshAPIView.as_view()),
]
