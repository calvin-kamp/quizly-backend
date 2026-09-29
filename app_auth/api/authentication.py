"""Cookie-based JWT authentication."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate requests with the JWT from the ``access_token`` cookie.

    Works like ``JWTAuthentication``, but reads the token from a cookie instead
    of the ``Authorization`` header.
    """

    def authenticate(self, request):
        """Return ``(user, token)`` for a valid cookie.

        Returns ``None`` if the request has no ``access_token`` cookie.

        Raises:
            InvalidToken: If the cookie holds an invalid or expired token.
        """
        raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token
