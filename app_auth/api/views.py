"""Views for registration, login, logout and token refresh.

The JWT are sent in ``HttpOnly`` cookies named ``access_token`` and
``refresh_token``.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from ..utils import delete_auth_cookies, set_auth_cookie, set_login_cookies
from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    """Create a new user account. Public endpoint."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Register a user. Answers 201, or 400 for invalid data."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "detail": "User created successfully!",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Log in and set the ``access_token`` and ``refresh_token`` cookies."""

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate the user and store both tokens in cookies.

        The tokens are removed from the response body, which only contains
        ``detail`` and ``user``. Answers 401 for wrong credentials.
        """
        response = super().post(request, *args, **kwargs)
        tokens = response.data

        set_login_cookies(response, tokens)
        response.data = {
            "detail": "Login successfully!",
            "user": tokens.get("user"),
        }

        return response


class LogoutView(TokenBlacklistView):
    """Log out: invalidate the refresh token and delete both cookies."""

    def post(self, request: Request, *args, **kwargs):
        """Blacklist the refresh token from the cookie and delete the cookies.

        Always answers 200, also when there are no cookies or the token is
        already invalid.
        """
        self._blacklist_refresh_cookie(request)

        response = Response(
            {
                "detail": (
                    "Log-Out successfully! All Tokens will be deleted. "
                    "Refresh token is now invalid."
                ),
            },
            status=status.HTTP_200_OK,
        )
        delete_auth_cookies(response)

        return response

    def _blacklist_refresh_cookie(self, request):
        """Blacklist the token of the ``refresh_token`` cookie, if any."""
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            pass


class CookieTokenRefreshView(TokenRefreshView):
    """Issue a new access token based on the ``refresh_token`` cookie."""

    def post(self, request: Request, *args, **kwargs):
        """Validate the refresh cookie and set a new ``access_token`` cookie.

        Raises:
            InvalidToken: If the refresh cookie is missing, expired or invalid
                (answers 401).
        """
        response = Response(
            {"detail": "Token refreshed"},
            status=status.HTTP_200_OK,
        )
        set_auth_cookie(
            response,
            "access_token",
            self._get_new_access_token(request),
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
        )

        return response

    def _get_new_access_token(self, request):
        """Return a new access token for the refresh token in the cookie."""
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise InvalidToken("Kein Refresh-Token vorhanden.")

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        return serializer.validated_data["access"]
