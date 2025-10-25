from __future__ import annotations
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "patronymic", "password", "password2")

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match"})
        return data

    def create(self, validated):
        pwd = validated.pop("password")
        validated.pop("password2", None)
        user = User.objects.create_user(**validated, password=pwd)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email, password = data.get("email"), data.get("password")
        user = authenticate(username=email, password=password)
        if not user:
            # If we don't rely on Django's ModelBackend, do manual check:
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
            if not user_obj.check_password(password) or not user_obj.is_active:
                raise serializers.ValidationError("Invalid credentials")
            data["user"] = user_obj
            return data
        if not user.is_active:
            raise serializers.ValidationError("User is inactive")
        data["user"] = user
        return data


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "patronymic", "is_active")
        read_only_fields = ("id", "email", "is_active")
