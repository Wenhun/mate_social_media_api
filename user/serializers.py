from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

from django.contrib.auth.models import AbstractUser


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "password", "is_staff")
        read_only_fields = ("is_staff",)

    def create(self, validated_data: dict) -> AbstractUser:
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance: AbstractUser, validated_data: dict) -> AbstractUser:
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user
