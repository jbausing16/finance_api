from rest_framework import (
    viewsets,
    status
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from core import models as core_models
from django.utils import timezone
from users import serializers as u_ser
# from django.db.models import Q
# from django.db.models.functions import Lower
from app.authentication import CookieJWTAuthentication
from core.core_functions import Core as super_f
import json
# import requests
# from django.conf import settings
from email.message import EmailMessage
from django.core.mail import send_mail


class UsersView(viewsets.ModelViewSet):
    """
    GET /api/warehouse/expense
    """
    ph_timezone = timezone.get_fixed_timezone(480)
    current_time_ph = timezone.localtime(
        timezone.now(), ph_timezone)
    queryset = core_models.UserAcc.objects.all()
    serializer_class = u_ser.AccountSerializer

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'check_email':
            return [AllowAny()]
        elif self.action == 'check_pin':
            return [AllowAny()]
        elif self.action == 'change_pass':
            return [AllowAny()]
        return super().get_permissions()

    @action(methods=['GET'], detail=False)
    def view_user_account(self, request):
        """
        <GET> /api/users/{user_id}/view_user_account
        """
        user_account = core_models.UserAcc.objects.filter(
            user=request.user
        ).first()

        if not user_account:
            return Response(
                {"success": False, "message": "User account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = u_ser.AccountSerializer(user_account, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def check_email(self, request):
        """
        <GET> /api/users/check_email
        """
        email = request.query_params.get("email")
        user = core_models.User.objects.filter(
            email=email
        ).first()

        if not user:
            return Response(
                {"success": False, "message": "Email is not registered."},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            newPin = super_f.generate_int(6)
            userPin = core_models.ChangePass.objects.filter(
                user=user
            ).first()
            if userPin:
                userPin.pin = newPin
                userPin.save()
            else:
                pin_save = core_models.ChangePass(
                    user=user,
                    pin=newPin
                )
                pin_save.save()

            plain_text_body = "OTP - Finance System"
            # Create the email object
            em = EmailMessage()
            em['From'] = "One Outsourse Direct Corporation"
            em['To'] = email
            em['Subject'] = "OTP - Finance System"
            em.set_content(plain_text_body)

            send_mail(
                subject="OTP - Finance System",
                message=plain_text_body,
                from_email="no-reply@oneapp.ph",
                recipient_list=[email],
                fail_silently=False,
                html_message=f"Your One Time PIN is {newPin}."
            )

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def check_pin(self, request):
        """
        <GET> /api/users/check_pin
        """
        email = request.query_params.get("email")
        pin = request.query_params.get("pin")
        c_pin = core_models.ChangePass.objects.filter(
            user__email=email,
            pin=pin
        ).first()

        if not c_pin:
            return Response(
                {"success": False, "message": "OTP does not match."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def change_pass(self, request):
        """
        <GET> /api/users/change_pass
        """
        data = request.data
        p_data = json.loads(data['data'])
        email = p_data.get("email")
        passw = p_data.get("pass")
        pin = p_data.get("pin")
        # print(data)
        # print(email)
        # print(passw)
        # print(pin)
        check_user = core_models.ChangePass.objects.filter(
            user__email=email,
            pin=pin
        )

        if not check_user:
            return Response(
                {"success": False, "message": "Invalid Action"},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            user = core_models.User.objects.filter(
                email=email
            ).first()
            user.set_password(passw)
            user.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)
