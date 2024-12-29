from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from django.conf import settings
import requests
import secrets
from .models import PlatformAccess
from .serializers import PlatformAccessSerializer
import logging

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retrieve the current user's platform access status.
        """
        try:
            platform_access = PlatformAccess.objects.get(user=request.user)
            serializer = PlatformAccessSerializer(platform_access)
            return Response(serializer.data)
        except PlatformAccess.DoesNotExist:
            return Response(
                {"error": "You have not paid for the platform"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request):
        """
        Initialize a payment or retry a failed/pending payment
        """
        try:
            # Retrieve the user's existing platform access
            platform_access = PlatformAccess.objects.get(user=request.user)

            if platform_access.status == "SUCCESS":
                return Response(
                    {"error": "You already have access to the platform"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate a new reference for retry
            platform_access.reference = f"platform-access-{secrets.token_hex(16)}"
            platform_access.status = "PENDING"
            platform_access.save()

        except PlatformAccess.DoesNotExist:
            # Create a new record for the user
            platform_access = PlatformAccess.objects.create(
                user=request.user,
                reference=f"platform-access-{secrets.token_hex(16)}",
                amount=settings.PLATFORM_ACCESS_FEE,
                status="PENDING",
            )

        # Prepare payment initialization data
        amount = settings.PLATFORM_ACCESS_FEE
        email = request.user.email
        reference = platform_access.reference

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "amount": int(float(amount) * 100),
            "email": email,
            "reference": reference,
            "callback_url": f"{settings.FRONTEND_URL}/payment/verify",
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=data, headers=headers
        )

        if response.status_code == 200:
            response_data = response.json()

            return Response(
                {
                    "payment_url": response_data["data"]["authorization_url"],
                    "reference": reference,
                }
            )

        logger.error(f"Paystack initialization failed: {response.json()}")
        return Response(
            {"error": "Could not initialize payment"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    reference = (
        request.data.get("reference")
        or request.query_params.get("reference")
        or request.data.get("trxref")
        or request.query_params.get("trxref")
    )
    if not reference:
        return Response(
            {"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        platform_access = PlatformAccess.objects.get(
            user=request.user, reference=reference
        )

        # Verify payment with Paystack
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
        )

        if response.status_code == 200:
            response_data = response.json()

            if response_data["data"]["status"] == "success":
                platform_access.status = "SUCCESS"
                platform_access.verified_at = response_data["data"]["paid_at"]
                platform_access.save()

                return Response(
                    {"message": "Payment verified successfully", "status": "SUCCESS"}
                )

        platform_access.status = "FAILED"
        platform_access.save()
        return Response(
            {"message": "Payment verification failed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except PlatformAccess.DoesNotExist:
        return Response(
            {"error": "Payment not found"}, status=status.HTTP_400_BAD_REQUEST
        )
