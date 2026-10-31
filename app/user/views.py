"""
Views for the user API
"""
from rest_framework import generics, status  # authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import (
    UserSerializer, AuthTokenSerializer, UserIdSerializer
)
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.http import JsonResponse
from app.authentication import CookieJWTAuthentication
from uuid import uuid4
# import requests
# from django.conf import settings
from core import models as core_m
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q


ACCESS_COOKIE_MAX_AGE = 15 * 60
REFRESH_COOKIE_MAX_AGE = 24 * 60 * 60
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = "None"


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserIdSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    session_uuid = str(user.session_uuid)
    refresh['sid'] = session_uuid
    access_token = refresh.access_token
    access_token['sid'] = session_uuid

    return {
        'refresh': str(refresh),
        'access': str(access_token),
    }


def set_auth_cookies(response, access_token, refresh_token=None):
    response.set_cookie(
        'access_token', access_token,
        max_age=ACCESS_COOKIE_MAX_AGE,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE
    )

    if refresh_token is not None:
        response.set_cookie(
            'refresh_token', refresh_token,
            max_age=REFRESH_COOKIE_MAX_AGE,
            httponly=True,
            secure=AUTH_COOKIE_SECURE,
            samesite=AUTH_COOKIE_SAMESITE
        )


def clear_auth_cookies(response):
    response.set_cookie(
        'access_token', '',
        max_age=0,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE
    )
    response.set_cookie(
        'refresh_token', '',
        max_age=0,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE
    )


@api_view(['POST'])
def login(request):
    user = get_object_or_404(
        core_m.User,
        Q(username=request.data['email']) |
        Q(email=request.data['email'])
    )

    if not user.check_password(request.data['password']):
        return Response({
            "message": "Wrong password."
        }, status=status.HTTP_404_NOT_FOUND)

    # Rotating session UUID invalidates prior session tokens for this user.
    user.session_uuid = uuid4()
    user.save(update_fields=['session_uuid'])

    tokens = get_tokens_for_user(user)

    role = core_m.Access.objects.filter(
        role=user.user_acc.first().role,
        access=True
    ).order_by('id').first()

    response = JsonResponse({
        "message": "Login successful",
        "success": True,
        "uid": user.id,
        "rid": user.user_acc.first().user_type.id,
        "land": role.module.id
        })

    set_auth_cookies(response, tokens['access'], tokens['refresh'])
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([CookieJWTAuthentication])
def me(request):
    user = request.user
    role = core_m.Access.objects.filter(
        role=user.user_acc.first().role,
        access=True
    ).order_by('id').first()
    print("Cookies:", request.COOKIES)
    print("Access Token Cookie:", request.COOKIES.get('access_token'))
    return Response({
        "success": True,
        "data": user.id,
        "land": role.module.id
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([CookieJWTAuthentication])
def logout(request):
    response = JsonResponse({"message": "Logout successful"})
    clear_auth_cookies(response)
    return response


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token')

    if not refresh_token:
        response = Response(
            {
                'detail': 'Refresh token missing',
                'reason': 'refresh_missing'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
        clear_auth_cookies(response)
        return response

    try:
        refresh = RefreshToken(refresh_token)
        user_id = refresh.get('user_id')
        token_session_uuid = str(refresh.get('sid', ''))

        if not user_id or not token_session_uuid:
            response = Response(
                {
                    'detail': 'Invalid refresh token session.',
                    'reason': 'refresh_invalid'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
            clear_auth_cookies(response)
            return response

        user = core_m.User.objects.filter(id=user_id).first()
        if not user:
            response = Response(
                {
                    'detail': 'Refresh token user does not exist.',
                    'reason': 'refresh_invalid'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
            clear_auth_cookies(response)
            return response

        if str(user.session_uuid) != token_session_uuid:
            response = Response(
                {
                    'detail': 'You were logged out because your account signed in elsewhere.',
                    'reason': 'logged_in_elsewhere'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
            clear_auth_cookies(response)
            return response

        new_access_token = refresh.access_token
        new_access_token['sid'] = token_session_uuid
        new_access = str(new_access_token)

        response = Response({"access": new_access}, status=status.HTTP_200_OK)
        set_auth_cookies(response, new_access)

        return response

    except TokenError as e:
        response = Response(
            {
                'detail': f"Invalid refresh token {e}",
                'reason': 'refresh_invalid'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
        clear_auth_cookies(response)
        return response
