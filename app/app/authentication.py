from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        if request.path == '/api/user/login/':
            return None

        header = self.get_header(request)

        if header is None:
            raw_token = request.COOKIES.get(
                settings.SIMPLE_JWT.get('AUTH_COOKIE')
            )
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        token_session_uuid = str(validated_token.get('sid', ''))
        user_session_uuid = str(getattr(user, 'session_uuid', ''))

        if not token_session_uuid or token_session_uuid != user_session_uuid:
            raise AuthenticationFailed({
                "detail": "Your session is no longer valid.",
                "reason": "logged_in_elsewhere"
            })

        return user, validated_token
