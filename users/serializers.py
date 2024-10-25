from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, MDA


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
