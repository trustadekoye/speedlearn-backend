from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    MDASerializer,
)
from .models import CustomUser, MDA


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


class MDAView(generics.ListAPIView):
    queryset = MDA.objects.all()
    serializer_class = MDASerializer
    permission_classes = [permissions.AllowAny]
