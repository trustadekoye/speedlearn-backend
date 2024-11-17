from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, verify_payment

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("verify-payment/", verify_payment, name="verify_payment"),
    path("", include(router.urls)),
]
