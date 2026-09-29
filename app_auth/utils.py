"""Helper functions of the authentication views."""

from django.conf import settings


def set_auth_cookie(response, key, value, lifetime):
    """Store a token in an ``HttpOnly`` cookie of the response.

    Args:
        response: The response that carries the cookie.
        key: Name of the cookie, ``access_token`` or ``refresh_token``.
        value: The token.
        lifetime: How long the cookie is valid, as ``timedelta``.
    """
    response.set_cookie(
        key=key,
        value=value,
        max_age=lifetime,
        secure=settings.AUTH_COOKIE["SECURE"],
        httponly=True,
        samesite=settings.AUTH_COOKIE["SAMESITE"],
    )


def set_login_cookies(response, tokens):
    """Store the refresh and the access token of a login in cookies.

    Args:
        response: The response that carries the cookies.
        tokens: Dictionary with the keys ``refresh`` and ``access``.
    """
    set_auth_cookie(
        response,
        "refresh_token",
        tokens.get("refresh"),
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
    )
    set_auth_cookie(
        response,
        "access_token",
        tokens.get("access"),
        settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
    )


def delete_auth_cookies(response):
    """Delete the ``access_token`` and ``refresh_token`` cookies."""
    for key in ("refresh_token", "access_token"):
        response.delete_cookie(
            key=key,
            samesite=settings.AUTH_COOKIE["SAMESITE"],
        )
