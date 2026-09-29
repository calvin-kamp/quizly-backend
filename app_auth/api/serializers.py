"""Serializers for registration and login."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validate and create a new user.

    Expects ``username``, ``email``, ``password`` and ``confirmed_password``.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "confirmed_password")
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        """Reject an email address that is already in use (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def validate(self, data):
        """Check that both passwords match and pass Django's validators."""
        if data["password"] != data["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )

        validate_password(data["password"])

        return data

    def create(self, validated_data):
        """Create the user with a hashed password.

        ``confirmed_password`` is only used for validation and is not stored.
        """
        validated_data.pop("confirmed_password")

        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Validate the login credentials and add the user data to the response."""

    def validate(self, attrs):
        """Return the token pair extended by a ``user`` entry.

        The entry contains the ``id``, ``username`` and ``email`` of the user.
        """
        data = super().validate(attrs)
        data.update(
            {
                "user": {
                    "id": self.user.id,
                    "username": self.user.username,
                    "email": self.user.email,
                }
            }
        )

        return data
