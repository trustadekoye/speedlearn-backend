from rest_framework import serializers, status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    MDASerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
)
from .models import CustomUser, MDA
import logging

logger = logging.getLogger(__name__)


# User Registration View
class UserRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Tok
        Create a new user.
        """
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "user": UserRegisterSerializer(user).data,
                    "token": token.key,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Login View
class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Login a user.
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get user details.
        """
        user = request.user
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Update user details.
        """
        user = request.user
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                email = serializer.validated_data["email"]
                user = CustomUser.objects.get(email=email)

                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Create password reset link
                reset_link = (
                    f"{settings.FRONTEND_URL}/password-reset/confirm/{uid}/{token}/"
                )

                # Send email to user
                try:
                    send_mail(
                        "Password Reset Request",
                        f"Click the following link to reset your password: {reset_link}",
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                except Exception as e:
                    return Response(
                        {"detail": "Unable to send password reset email"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                return Response(
                    {"detail": "Password reset email sent"}, status=status.HTTP_200_OK
                )
        except serializers.ValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()

                try:
                    send_mail(
                        subject="Password Reset Confrimation",
                        message=f"Your password has been reset successfully.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Failed to send password reset email: {e}")

                return Response(
                    {"detail": "Password reset successfully."},
                    status=status.HTTP_200_OK,
                )

        except serializers.ValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MDAView(generics.ListAPIView):
    queryset = MDA.objects.all()
    serializer_class = MDASerializer
    permission_classes = [permissions.AllowAny]
