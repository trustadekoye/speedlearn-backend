from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, MDA
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


# Ministries, Departments and Agencies
class MDASerializer(serializers.ModelSerializer):
    class Meta:
        model = MDA
        fields = ("id", "name")


# User Registration
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    mda = serializers.PrimaryKeyRelatedField(queryset=MDA.objects.all())

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "mda",
            "phone_number",
            "is_officer",
            "is_admin",
            "date_joined",
        )
        read_only_fields = ("date_joined",)

    def create(self, validated_data):
        """
        Create and return a new `User` instance, given the validated data.
        """
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_officer=True,
            mda=validated_data.get("mda"),
            phone_number=validated_data.get("phone_number", ""),
        )
        return user


# User Login
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user is not None:
            return user
        raise serializers.ValidationError("Invalid email or password")


class UserSerializer(serializers.ModelSerializer):
    mda = serializers.StringRelatedField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "mda",
            "phone_number",
            "is_officer",
            "is_admin",
        )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        # Check if user exists with this email
        email = data.get("email")
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        data["user"] = user
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uidb64 = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, data):
        if data.get("new_password") != data.get("confirm_password"):
            raise serializers.ValidationError(
                {"password_mismatch": "The two password fields didn't match."}
            )
        try:
            uid = urlsafe_base64_decode(data.get("uidb64")).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError(
                {"invalid_reset_link": "Invalid reset link."}
            )

        # Verify token
        if not default_token_generator.check_token(user, data.get("token")):
            raise serializers.ValidationError("Invalid or expired reset link.")

        # Add user to validated data
        data["user"] = user
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        user.set_password(validated_data["new_password"])
        user.save()
        return user
