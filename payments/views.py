from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from django.conf import settings
import requests
import secrets
from .models import PlatformAccess
from .serializers import PlatformAccessSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PlatformAccessSerializer

    def get_queryset(self):
        return PlatformAccess.objects.filter(user=self.request.user)

    def create(self, request):
        # Check if user has already paid
        existing_access = PlatformAccess.objects.filter(
            user=request.user, status="SUCCESS"
        ).exists()

        if existing_access:
            return Response(
                {"error": "You already have access to the platform"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = settings.PLATFORM_ACCESS_FEE
        email = request.user.email
        reference = f"platform-access-{secrets.token_hex(16)}"

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

            # Create a platform access record
            PlatformAccess.objects.create(
                user=request.user, amount=amount, reference=reference
            )

            return Response(
                {
                    "payment_url": response_data["data"]["authorization_url"],
                    "reference": reference,
                }
            )

        return Response(
            {
                "error": "Could not initialize payment",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    reference = request.data.get("reference")

    try:
        platform_access = PlatformAccess.objects.get(reference=reference)

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
                platform_access.save()

                return Response({"message": "Payment verified successfully"})

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
