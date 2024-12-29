from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status


def payment_required_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    response = exception_handler(exc, context)

    if isinstance(exc, PermissionDenied):
        # Check if the error is from HasPaidPlatformAccess permission
        try:
            if hasattr(exc, "detail") and "payment required" in str(exc.detail).lower():
                return Response(
                    {
                        "error": "Payment required",
                        "message": "Please complete payment to access this feature",
                        "payment_required": True,
                        "payment_url": "/api/payments/initialize",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except:
            pass

        return response
