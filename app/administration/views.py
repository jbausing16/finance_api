from rest_framework import (
    viewsets,
    status
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core import models as core_models
from django.utils import timezone
from administration import serializers as u_ser
from django.db.models import Q, Min
# from django.db.models.functions import Lower
from app.authentication import CookieJWTAuthentication
# import requests
# from django.conf import settings
import json
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from core.core_functions import Core as super
from django.db.models import (
    Sum, F, Value, DecimalField, IntegerField, Case, When
)
from django.db.models.functions import Coalesce
from decimal import Decimal
from rest_framework.exceptions import PermissionDenied
from datetime import timedelta, datetime


class AdministrationsView(viewsets.ModelViewSet):
    """
    GET /api/warehouse/expense
    """
    ph_timezone = timezone.get_fixed_timezone(480)
    current_time_ph = timezone.localtime(
        timezone.now(), ph_timezone)
    queryset = ""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['GET'], detail=False)
    def get_acc_types(self, request, pk=None):
        """
        <GET> /api/administration/get_acc_types
        """
        accTypes = core_models.AccCateg.objects.filter(
            client=request.user.user_acc.first().client,
            status=1
        ).order_by('id')

        serializer = u_ser.AccCategSerializer(accTypes, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def get_accounts(self, request, pk):
        """
        <GET> /api/administration/get_accounts
        """
        acc = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            category__id=pk
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        ).exclude(parent=0).order_by("code")

        serializer = u_ser.AccountsSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_banks(self, request):
        """
        <GET> /api/administration/get_banks
        """
        search = request.query_params.get("search")
        acc = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            cash=True,
            status=1
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )
        if search:
            acc = acc.filter(
                name__icontains=search
            )

        acc = acc.order_by('id')

        serializer = u_ser.AccountsSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_bank(self, request):
        """
        <GET> /api/administration/up_bank
        """
        data = request.data
        p_data = json.loads(data['datas'])
        # print(p_data)

        acc = core_models.Accounts.objects.filter(
            id=p_data.get("id")
        ).first()

        acc.check_no = p_data.get("check_no")
        acc.status = p_data.get("status")

        acc.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_wtax(self, request):
        """
        <GET> /api/administration/get_wtax
        """
        acc = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            wtax=True
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )
        serializer = u_ser.AccountsSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_all_accounts(self, request):
        """
        <GET> /api/administration/get_all_accounts
        """
        acc = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
        ).order_by("code")

        serializer = u_ser.AccountsAllSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_account(self, request, pk=None):
        """
        <GET> /api/administration/add_account
        """
        data = request.data
        p_data = json.loads(data['datas'])
        # print(p_data)

        categ = core_models.AccCateg.objects.get(
            id=p_data.get("category")
        )

        acc = core_models.Accounts(
            client=request.user.user_acc.first().client,
            category=categ,
            code=p_data.get("code"),
            name=p_data.get("name"),
            cash=True if p_data.get("cash") == 1 else False,
            wtax=True if p_data.get("wtax") == 1 else False,
            parent=p_data.get("parent"),
            type=p_data.get("type"),
            level=p_data.get("level"),
            balance=0
        )
        acc.save()

        if int(p_data.get("wtax")) == 1:
            add_e = core_models.AutoEntries(
                client=request.user.user_acc.first().client,
                module="Wtax",
                type="",
                account=acc,
                rate=0
            )
            add_e.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_account(self, request):
        """
        <GET> /api/administration/up_account
        """
        data = request.data
        p_data = json.loads(data['datas'])
        # print(p_data)

        acc = core_models.Accounts.objects.filter(
            id=p_data.get("id")
        ).first()

        acc.code = p_data.get("code")
        acc.name = p_data.get("name")
        acc.cash = True if p_data.get("cash") == 1 else False
        acc.wtax = True if p_data.get("wtax") == 1 else False
        acc.parent = p_data.get("parent")
        acc.type = p_data.get("type")
        acc.level = p_data.get("level")
        acc.status = p_data.get("status")

        acc.save()

        if int(p_data.get("wtax")) == 1:
            check = core_models.AutoEntries.objects.filter(
                account=acc,
                module="Wtax"
            )
            if check:
                stat = 2
                if int(p_data.get("status")) == 1:
                    stat = 1
                for che in check:
                    che.status = stat
                    che.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_roles(self, request):
        """
        <GET> /api/administration/get_roles
        """
        cid = request.query_params.get("cid")

        if cid:
            roles = core_models.Roles.objects.filter(
                client__id=int(cid)
            )
        else:
            roles = core_models.Roles.objects.filter(
                client=request.user.user_acc.first().client
            )

        serializer = u_ser.RoleSerializer(roles, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_types(self, request):
        """
        <GET> /api/administration/get_types
        """
        user = request.user.user_acc.first()
        if user.user_type.id == 1:
            types = core_models.Types.objects.all()
        else:
            types = core_models.Types.objects.all().exclude(
                id=1
            )

        serializer = u_ser.TypesSerializer(types, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_clients(self, request):
        """
        <GET> /api/administration/get_clients
        """
        user = request.user.user_acc.first()
        if user.user_type.id == 1:
            types = core_models.Client.objects.all()
        else:
            types = core_models.Client.objects.filter(
                id=user.client.id
            )

        serializer = u_ser.ClientSerializer(types, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # @action(methods=['POST'], detail=False)
    # def add_user(self, request, pk=None):
    #     """
    #     <GET> /api/administration/add_user
    #     """
    #     data = json.loads(request.data.get("datas", "{}"))

    #     # Merge JSON data + file data into one dict
    #     incoming = {**data, **request.FILES}

    #     serializer = u_ser.UserCreateSerializer(data=incoming)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()

    #     return Response({"success": True}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_user(self, request, pk=None):
        """
        <GET> /api/administration/add_account
        """
        data = request.data
        p_data = json.loads(data['datas'])
        # print(p_data)
        profile = request.FILES.get('profile')
        sign = request.FILES.get('sign')
        client = core_models.Client.objects.get(
            id=p_data.get("client")
            )
        type = core_models.Types.objects.get(
            id=p_data.get("type")
            )
        role = core_models.Roles.objects.get(
            id=p_data.get("role")
            )

        email_exists = core_models.User.objects.filter(
            email=p_data.get("email")
        ).exists()
        uname_exists = core_models.User.objects.filter(
            username=p_data.get("username")
        ).exists()

        if email_exists or uname_exists:
            message_parts = []
            if email_exists:
                message_parts.append(
                    "Email is already associated with other account."
                )
            if uname_exists:
                message_parts.append(
                    "Username is already associated with other account."
                )
            return Response({
                "success": False,
                "message": ", ".join(message_parts)
            }, status=status.HTTP_200_OK)

        c_user = core_models.UserAcc.objects.filter(
            client=client,
            status=1
        )
        current = c_user.count()
        if client.license < current:
            mes = "Cannot create a new user."
            mes1 = f"License limit ({client.license}) has been reached."
            mes2 = "You can set other users to 'Inactive' to proceed."
            return Response({
                "success": False,
                "message": f"{mes} {mes1} {mes2}"
            }, status=status.HTTP_200_OK)

        with transaction.atomic():
            acc = core_models.User(
                email=p_data.get("email"),
                first_name=p_data.get("fname"),
                last_name=p_data.get("lname"),
                username=p_data.get("username"),
                )
            acc.set_password(p_data.get("password"))
            acc.save()

            if acc:
                accU = core_models.UserAcc(
                    user=acc,
                    client=client,
                    phone=p_data.get("phone"),
                    user_type=type,
                    job_position=p_data.get("position"),
                    role=role
                    )
                if profile:
                    accU.profile = profile
                if sign:
                    accU.signature = sign
                accU.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_users(self, request):
        """
        <GET> /api/administration/get_users
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")

        user = request.user.user_acc.first()
        if user.user_type.id == 1:
            users = core_models.UserAcc.objects.all()
        else:
            users = core_models.UserAcc.objects.filter(
                client=request.user.user_acc.first().client
            )

        if search:
            users = users.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search)
            )

        users = users.order_by("id")

        result_page = paginator.paginate_queryset(users, request)
        serializer = u_ser.UserSerializer(result_page, many=True)

        # return Response({
        #     "success": True,
        #     "data": serializer.data
        # }, status=status.HTTP_200_OK)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_users_client(self, request):
        """
        <GET> /api/administration/get_users_client
        """

        users = core_models.UserAcc.objects.filter(
            client=request.user.user_acc.first().client
        ).order_by("id")

        serializer = u_ser.UserClientSerializer(users, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_user(self, request, pk=None):
        """
        <GET> /api/administration/up_user
        """
        data = request.data
        p_data = json.loads(data['datas'])
        # print(p_data)
        profile = request.FILES.get('profile')
        sign = request.FILES.get('sign')
        client = core_models.Client.objects.get(
            id=p_data.get("client")
            )
        type = core_models.Types.objects.get(
            id=p_data.get("type")
            )
        role = core_models.Roles.objects.get(
            id=p_data.get("role")
            )

        accU = core_models.UserAcc.objects.get(
                id=int(p_data.get("id"))
            )

        checkUser = core_models.User.objects.filter(
            email=p_data.get("email")
        ).exclude(id=p_data.get("id"))

        with transaction.atomic():
            if checkUser:
                return Response(
                    {"success": False,
                     "message": "Email was used by another user"},
                    status=status.HTTP_200_OK
                )

            if accU:
                accU.client = client
                accU.phone = p_data.get("phone")
                accU.user_type = type
                accU.job_position = p_data.get("position")
                accU.role = role
                accU.status = int(p_data.get("status"))

            if profile:
                accU.profile = profile
            if sign:
                accU.signature = sign
            accU.save()

            acc = core_models.User.objects.get(
                id=accU.user.id
            )
            if acc:
                acc.email = p_data.get("email")
                acc.first_name = p_data.get("fname")
                acc.last_name = p_data.get("lname")

            if p_data.get("password"):
                acc.set_password(p_data.get("password"))
            acc.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_approvals(self, request):
        """
        <GET> /api/administration/get_approvals
        """
        search = request.query_params.get("search")
        app = core_models.Approval.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            app = app.filter(
                module__icontains=search
            )
        app = app.order_by("id")

        serializer = u_ser.ApprovalSerializer(app, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_approval(self, request, pk=None):
        """
        <GET> /api/administration/up_approval
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            app = core_models.Approval.objects.get(
                id=int(p_data.get("id"))
            )
            if app:
                if p_data.get("user") is not None:
                    user = core_models.UserAcc.objects.get(
                        id=p_data.get("user")
                    )
                    if user:
                        app.user = user
                app.status = p_data.get("status")
                app.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_auto_entries(self, request):
        """
        <GET> /api/administration/get_auto_entries
        """
        search = request.query_params.get("search")
        auto = core_models.AutoEntries.objects.filter(
            client=request.user.user_acc.first().client,
            status=1
        )

        if search:
            auto = auto.filter(
                module__icontains=search
            )
        auto = auto.order_by("id")

        serializer = u_ser.AutoEntriesSerializer(auto, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_auto_entries(self, request, pk=None):
        """
        <GET> /api/administration/up_auto_entries
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            aut = core_models.AutoEntries.objects.get(
                id=int(p_data.get("id"))
            )
            if aut:
                account = core_models.Accounts.objects.get(
                    id=int(p_data.get("account"))
                )
                aut.type = p_data.get("type")
                aut.account = account
                if p_data.get("rate") and float(p_data.get("rate")) > 0:
                    aut.rate = p_data.get("rate")
                aut.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_period(self, request):
        """
        <POST> /api/administration/add_period
        """
        data = request.data
        p_data = json.loads(data['datas'])

        client = request.user.user_acc.first().client

        with transaction.atomic():
            duplicate = 0
            dups = []
            for dat in p_data:
                new_from = dat.get("from")
                new_to = dat.get("to")

                # Check if overlaps exist
                overlapping = core_models.PostingPeriod.objects.filter(
                    client=client,
                    is_deleted=False
                ).filter(
                    Q(from_date__lte=new_to) & Q(to_date__gte=new_from)
                )

                if overlapping.exists():
                    duplicate += 1
                    dups.append(dat.get('p_period'))

            if duplicate == 0:
                # Save only if no overlap
                for dat in p_data:
                    pperiod = core_models.PostingPeriod(
                        client=client,
                        year=dat.get("f_year"),
                        name=dat.get("p_period"),
                        from_date=dat.get("from"),
                        to_date=dat.get("to"),
                    )
                    pperiod.save()
            else:
                return Response({
                    "success": False,
                    "message": (
                        f"Incoming periods overlap with existing period(s): "
                        f"{', '.join(dups)}"
                    )}, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Posting periods saved successfully."
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_period(self, request):
        """
        <GET> /api/administration/up_period
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            period = core_models.PostingPeriod.objects.get(
                id=int(p_data.get("id"))
            )
            if period:
                period.status = int(p_data.get("status"))
                period.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_period(self, request):
        """
        <GET> /api/administration/get_period
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")

        period = core_models.PostingPeriod.objects.filter(
            client=request.user.user_acc.first().client,
            is_deleted=False
        )

        if search:
            period = period.filter(
                name__icontains=search
            )
        period = period.order_by("-from_date")

        result_page = paginator.paginate_queryset(period, request)
        serializer = u_ser.PostPeriodSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['PATCH'], detail=True)
    def del_period(self, request, pk):
        """
        <GET> /api/administration/del_period
        """
        with transaction.atomic():
            period = core_models.PostingPeriod.objects.get(
                id=int(pk)
            )
            if period:
                period.is_deleted = True
                period.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_terms(self, request):
        """
        <GET> /api/administration/get_ar_terms
        """
        acc = core_models.PaymentTermsAR.objects.filter(
            client=request.user.user_acc.first().client
        )
        serializer = u_ser.ARPaymentSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def region_list(self, request, pk=None):
        """
        <GET> /api/administration/region_list
        """
        serializer = u_ser.RegionSerializer(
            instance=core_models.Region.objects.all(

            ).order_by('id'),
            many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def province_list(self, request, pk=None):
        """
        <GET> /api/administration/<region_id>/province_list
        """
        serializer = u_ser.ProvinceSerializer(
            instance=core_models.Province.objects.filter(
                region__id=pk
            ).order_by('id'),
            many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def city_list(self, request, pk=None):
        """
        <GET> /api/administration/<province_id>/city_list
        """
        serializer = u_ser.CitySerializer(
            instance=core_models.Municipality.objects.filter(
                province__id=pk
            ).order_by('id'),
            many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def barangay_list(self, request, pk=None):
        """
        <GET> /api/administration/<city_id>/barangay_list
        """
        serializer = u_ser.BarangaySerializer(
            instance=core_models.Barangay.objects.filter(
                municipality__id=pk
            ).order_by('id'),
            many=True)

        return Response({
            "success": True,
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_bp(self, request):
        """
        <GET> /api/administration/add_bp
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            bp = core_models.BusinessPartner(
                client=request.user.user_acc.first().client,
                type=int(p_data.get("type")),
                code=p_data.get("code"),
                name=p_data.get("name"),
                tin=p_data.get("tin"),
                terms=int(p_data.get("terms")),
                tax_stat=int(p_data.get("tax"))
            )
            if p_data.get("wtax") != 0:
                wtax = core_models.AutoEntries.objects.get(
                    id=int(p_data.get("wtax"))
                )
                bp.wtax = wtax
            if p_data.get("tandc") != 0:
                tandc = core_models.PaymentTermsAR.objects.get(
                    id=int(p_data.get("tandc"))
                )
                bp.p_terms = tandc
            bp.save()

            bpadd = core_models.BPAddress(
                bp=bp,
                street=p_data.get("street"),
                zipcode=p_data.get("zipcode"),
                c_person=p_data.get("c_person"),
                c_no=p_data.get("c_no"),
                email=p_data.get("c_email")
            )
            if p_data.get("barangay") != 0:
                bara = core_models.Barangay.objects.get(
                    id=int(p_data.get("barangay"))
                )
                bpadd.barangay = bara
            bpadd.save()

            bpcon = core_models.BPContract(
                bp=bp,
                type=int(p_data.get("con_type")),
                c_person=p_data.get("con_person"),
                c_no=p_data.get("con_con"),
                email=p_data.get("con_email")
            )
            if p_data.get("con_start") != "":
                bpcon.start_date = p_data.get("con_start")
            if p_data.get("con_end") != "":
                bpcon.start_date = p_data.get("con_end")
            bpcon.save()

        return Response(
            {"success": True,
                "message": f"{p_data.get('name')} successfully added."},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_bp(self, request):
        """
        <GET> /api/administration/get_bp
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        filter = int(request.query_params.get("filter"))

        bp = core_models.BusinessPartner.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            bp = bp.filter(
                name__icontains=search
            )
        if filter != 0:
            bp = bp.filter(
                type=filter
            )

        bp = bp.order_by('-id')

        result_page = paginator.paginate_queryset(bp, request)
        serializer = u_ser.BPSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['PATCH'], detail=False)
    def up_bp(self, request):
        """
        <GET> /api/administration/up_bp
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            bp = core_models.BusinessPartner.objects.get(
                id=int(p_data.get("id"))
            )
            if bp:
                bp.type = int(p_data.get("type"))
                bp.code = p_data.get("code")
                bp.name = p_data.get("name")
                bp.tin = p_data.get("tin")
                bp.terms = int(p_data.get("terms"))
                bp.tax_stat = int(p_data.get("tax"))

                if p_data.get("wtax") != 0:
                    wtax = core_models.AutoEntries.objects.get(
                        id=int(p_data.get("wtax"))
                    )
                    bp.wtax = wtax
                else:
                    bp.wtax = None
                if p_data.get("tandc") != 0:
                    tandc = core_models.PaymentTermsAR.objects.get(
                        id=int(p_data.get("tandc"))
                    )
                    bp.p_terms = tandc
                else:
                    bp.p_terms = None
                bp.save()

                bpadd = core_models.BPAddress.objects.get(bp=bp)
                bpadd.street = p_data.get("street")
                bpadd.zipcode = p_data.get("zipcode")
                bpadd.c_person = p_data.get("c_person")
                bpadd.c_no = p_data.get("c_no")
                bpadd.email = p_data.get("c_email")

                if p_data.get("barangay") != 0:
                    bara = core_models.Barangay.objects.get(
                        id=int(p_data.get("barangay"))
                    )
                    bpadd.barangay = bara
                bpadd.save()

                bpcon = core_models.BPContract.objects.get(bp=bp)
                bpcon.type = int(p_data.get("con_type"))
                bpcon.c_person = p_data.get("con_person")
                bpcon.c_no = p_data.get("con_con")
                bpcon.email = p_data.get("con_email")

                if p_data.get("con_start") != "":
                    bpcon.start_date = p_data.get("con_start")
                if p_data.get("con_end") != "":
                    bpcon.start_date = p_data.get("con_end")
                bpcon.save()

        return Response(
            {"success": True,
                "message": f"{p_data.get('name')} updated successfully."},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_doc_no(self, request):
        """
        <GET> /api/administration/get_doc_no
        """
        search = request.query_params.get("search")
        docNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            docNo = docNo.filter(
                name__icontains=search
            )
        docNo = docNo.order_by("id")

        serializer = u_ser.DocNoSerializer(docNo, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False)
    def up_doc_no(self, request, pk=None):
        """
        <GET> /api/administration/up_doc_no
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            docNo = core_models.DocumentNo.objects.get(
                id=int(p_data.get("id"))
            )
            if docNo:
                docNo.no = p_data.get("no")
                docNo.save()

        return Response(
            {"success": True},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_autoDocNo(self, request):
        """
        <GET> /api/administration/get_autoDocNo
        """
        name = request.query_params.get("name")
        docNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client,
            name=name
        ).first()
        print(docNo)
        print(name)
        num = 0
        if docNo and docNo.no is not None and docNo.no != "":
            num = int(docNo.no) + int(1)

        return Response({
            "success": True,
            "no": num
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_bp_invoice(self, request):
        """
        <GET> /api/administration/get_bp_invoice
        """
        type = int(request.query_params.get("type"))
        bp = core_models.BusinessPartner.objects.filter(
            client=request.user.user_acc.first().client,
            type=type,
            status=1
        ).order_by('name')

        serializer = u_ser.BPCustSerializer(bp, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_wtax_rate(self, request):
        """
        <GET> /api/administration/get_wtax_rate
        """
        bp = core_models.AutoEntries.objects.filter(
            client=request.user.user_acc.first().client,
            module='Wtax',
            status=1
        ).order_by('type')

        serializer = u_ser.WtaxSerializer(bp, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_type(self, request):
        """
        <GET> /api/administration/get_account_type
        """
        acc = int(request.query_params.get("type"))
        ac = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            type=2
        )

        if acc != 0:
            ac = ac.filter(category__id=acc)

        ac = ac.order_by('name')

        serializer = u_ser.AccountCustSerializer(ac, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_type_head(self, request):
        """
        <GET> /api/administration/get_account_type_head
        """
        acc_type = int(request.query_params.get("type", 0))
        client = request.user.user_acc.first().client

        # Get all accounts for this client and type=1
        accounts_qs = core_models.Accounts.objects.filter(
            client=client
        )

        if acc_type != 0:
            accounts_qs = accounts_qs.filter(category=acc_type)

        accounts_qs = accounts_qs.order_by('code')

        # Build a parent -> children map
        children_map = {}
        for account in accounts_qs:
            if account.parent:
                children_map.setdefault(account.parent, []).append(account)

        # Get top-level accounts (parent is None or 0)
        top_accounts = [a for a in accounts_qs if not a.parent]

        # Pass the children map to serializer context
        serializer = u_ser.AccountCust1Serializer(
            top_accounts, many=True,
            context={'children_map': children_map})

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_type_head_ap(self, request):
        """
        <GET> /api/administration/get_account_type_head_ap
        """
        client = request.user.user_acc.first().client

        # Get all accounts for this client and type=1
        accounts_qs = core_models.Accounts.objects.filter(
            client=client
        )

        accounts_qs = accounts_qs.exclude(
            category__alias__in=["assets", "liabilities",
                                 "equity", "income", "other", "nonpost"]
        ).order_by('code')

        # Build a parent -> children map
        children_map = {}
        for account in accounts_qs:
            if account.parent:
                children_map.setdefault(account.parent, []).append(account)

        # Get top-level accounts (parent is None or 0)
        top_accounts = [a for a in accounts_qs if not a.parent]

        # Pass the children map to serializer context
        serializer = u_ser.AccountCust1Serializer(
            top_accounts, many=True,
            context={'children_map': children_map})

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_cash(self, request):
        """
        <GET> /api/administration/get_account_cash
        """
        ac = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            category=1,
            cash=True,
            type=2,
            status=1
        ).order_by('name')

        serializer = u_ser.AccountCustSerializer(ac, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_all(self, request):
        """
        <GET> /api/administration/get_account_all
        """
        ac = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            type=2
        ).order_by('name')

        serializer = u_ser.AccountCustSerializer(ac, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_auto_account(self, request):
        """
        <GET> /api/administration/get_auto_account
        """
        type = request.query_params.get("type")
        ac = core_models.AutoEntries.objects.filter(
            client=request.user.user_acc.first().client,
            type=type
        ).first()

        serializer = u_ser.WtaxSerializer(ac, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_ar_invoice(self, request):
        """
        <GET> /api/administration/add_ar_invoice
        """
        data = request.data
        p_data = json.loads(data['datas'])
        p_rows = json.loads(data['rows'])
        p_wtax = json.loads(data['wtax'])
        docType = int(data.get("docType"))
        # inv = p_data.get("invoice")
        print(data)
        # print(super.round2(data.get("vatAmt")))
        # print(super.round2(data.get("discount")))
        print(p_wtax)

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/R Invoice'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    # print("goods")
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Invoice Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Invoice Verifier"
                    )
                    bpartner = super.get_bp(id=p_data.get("cid")).first()
                    print(f"DocType here: {docType}")
                    ar = core_models.AROINV(
                        client=client,
                        code=bpartner,
                        bp_code=p_data.get("ccode"),
                        bp_name=p_data.get("cname"),
                        type=docType,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        receipt_date=p_data.get("receipt_date"),
                        po_num=p_data.get("po"),
                        remarks=p_data.get("remarks"),
                        price_bef_vat=super.round2(data.get("tbda")),
                        discount=super.round2(data.get("discount")),
                        vat=super.round2(data.get("vatAmt")),
                        wtax=super.round2(data.get("wtaxAmt")),
                        total=super.round2(data.get("total")),
                        added=request.user.user_acc.first()
                    )
                    if ver.status == 1:
                        ar.status = 5
                        end = "is awaiting your verification."
                        mess = f"A/R Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=2",
                            type=2
                        )
                    elif app.status == 1:
                        ar.status = 6
                        end = "is awaiting your approval."
                        mess = f"A/R Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=2",
                            type=2
                        )
                    else:
                        ar.status = 1
                    ar.save()

                    for rows in p_rows:
                        if rows.get("amount"):
                            ar1 = core_models.ARINV1(
                                ar=ar,
                                vatable=int(rows.get("vatable")),
                                wtax=int(rows.get("wtax")),
                                amount=super.round2(rows.get("amount"))
                            )
                            if docType == 2:
                                ar1.description = rows.get("description")
                                ar1.account = super.get_acc(
                                    int(rows.get("account")))
                            else:
                                prod = super.get_prod(int(rows.get("product")))
                                ar1.description = prod.name
                                ar1.account = prod.income
                                ar1.product = prod
                                ar1.price = super.round2(rows.get("price"))
                                ar1.qty = super.round2(rows.get("qty"))

                            if rows.get("customer") != "":
                                ar1.customer = super.get_cust(
                                    int(rows.get("customer")))
                            if rows.get("discount") != "":
                                ar1.discount = super.round2(
                                    rows.get("discount"))
                            ar1.save()

                    for rows in p_wtax:
                        if rows.get("code") != "0":
                            ar2 = core_models.ARINV2(
                                ar=ar,
                                wtax=super.get_ae(id=int(rows.get("code"))),
                                name=rows.get("name"),
                                rate=super.get_ae(
                                    id=int(rows.get("code"))).rate,
                                taxable_amt=rows.get("tax_amt"),
                                wtax_amt=rows.get("wtax_amt")
                            )
                            ar2.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=2,
                            origin_no=newInv,
                            remarks=f"Based on A/R Invoice {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=ar.id,
                            total=super.round2(data.get("total"))
                        )
                        ojdt.save()

                        ar_amt = super.round2(data.get("total"))
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account,
                            debit=ar_amt,
                            credit=0,
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=bpartner.id
                        )
                        ar = super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account
                        ar.balance += ar_amt
                        ar.save()

                        if super.round2(data.get("vatAmt")) > 0:
                            # vat_amt = ar_amt - (ar_amt / Decimal(1.12))
                            vat_amt = super.round2(data.get("vatAmt"))
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account,
                                debit=0,
                                credit=vat_amt,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=bpartner.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account
                            vat.balance += vat_amt
                            vat.save()

                        for rows in p_rows:
                            ramt = super.round2(rows.get("amount"))
                            rdis = super.round2(rows.get("discount"))
                            vat = Decimal("1.12")
                            print(f"Amt: {ramt}")
                            print(f"Disc: {ramt}")
                            print(f"Vat: {ramt}")
                            print(f"without VAT: {ramt / vat}")
                            print(f"without VAT 1: {super.round2(ramt / vat)}")
                            if int(rows.get("vatable")) == 1:
                                si = (super.round2(ramt / vat) - rdis)
                            else:
                                si = (ramt - rdis)
                            if rows.get("amount"):
                                if docType == 2:
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=super.get_acc(
                                            int(rows.get("account"))),
                                        debit=0,
                                        credit=si,
                                        remarks=rows.get("description"),
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    acc = super.get_acc(
                                        int(rows.get("account")))
                                    acc.balance += si
                                    acc.save()
                                else:
                                    prod = super.get_prod(
                                        int(rows.get("product")))
                                    ae = super.get_ae(
                                        client=client,
                                        type="Inventory Account"
                                    )
                                    mes = "Please select Inventory Account."
                                    if not ae.account and docType == 1:
                                        raise PermissionDenied(mes)
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=prod.income,
                                        debit=0,
                                        credit=si,
                                        remarks=prod.name,
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    prod.income.balance += si
                                    prod.income.save()

                                    amt = prod.cost * Decimal(rows.get("qty"))
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=prod.cogs,
                                        debit=amt,
                                        credit=0,
                                        remarks=prod.name,
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    prod.cogs.balance += si
                                    prod.cogs.save()

                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=ae.account,
                                        debit=0,
                                        credit=amt,
                                        remarks=prod.name,
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    ae.account.balance += si
                                    ae.account.save()

                                    upQ = core_models.Inventory.objects.filter(
                                        id=prod.id
                                    ).first()
                                    qty = super.round2(rows.get("qty"))
                                    upQ.stock -= qty
                                    upQ.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        # print(p_data)
        # print(p_rows)
        # print(p_wtax)

        return Response({
            "success": True,
            "message": f"Invoice {newInv} successfuly added."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def cancel_ar_invoice(self, request):
        """
        <GET> /api/administration/cancel_ar_invoice
        """
        data = request.data
        p_data = json.loads(data['datas'])
        id = int(data['currId'])

        ar = core_models.AROINV.objects.filter(id=id).first()

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/R Invoice - Cancelation'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    # print("goods")
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Invoice Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Invoice Verifier"
                    )

                    rem = ar.remarks
                    old_inv = p_data.get("invoice")
                    remarks = f"{rem} Cancellation of Invoice No. {old_inv}."
                    nar = core_models.AROINV(
                        client=client,
                        code=ar.code,
                        bp_code=ar.bp_code,
                        bp_name=ar.bp_name,
                        type=ar.type,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=ar.due_date,
                        doc_date=ar.doc_date,
                        po_num=ar.po_num,
                        remarks=remarks,
                        price_bef_vat=ar.price_bef_vat,
                        discount=ar.discount,
                        vat=ar.vat,
                        wtax=ar.wtax,
                        total=ar.total,
                        cancelation=True,
                        canceledAR=ar,
                        added=ar.added
                    )
                    if ver.status == 1:
                        nar.status = 5
                        # ar.status = 5
                    elif app.status == 1:
                        nar.status = 6
                        # ar.status = 6
                    else:
                        nar.status = 3
                        ar.status = 4
                    ar.save()
                    nar.save()

                    ar1 = core_models.ARINV1.objects.filter(ar=ar)
                    for rows in ar1:
                        nar1 = core_models.ARINV1(
                            ar=nar,
                            description=rows.description,
                            account=rows.account,
                            customer=rows.customer,
                            vatable=rows.vatable,
                            wtax=rows.wtax,
                            amount=rows.amount,
                            discount=rows.discount,
                            qty=rows.qty,
                            price=rows.price,
                            product=rows.product
                        )
                        nar1.save()

                    ar2 = core_models.ARINV2.objects.filter(ar=ar)
                    for rows in ar2:
                        nar2 = core_models.ARINV2(
                            ar=nar,
                            wtax=rows.wtax,
                            name=rows.name,
                            rate=rows.rate,
                            taxable_amt=rows.taxable_amt,
                            wtax_amt=rows.wtax_amt
                        )
                        nar2.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=2,
                            origin_no=newInv,
                            remarks=f"Based on A/R Invoice {newInv}",
                            post_date=nar.posting_date,
                            due_date=nar.due_date,
                            doc_date=nar.doc_date,
                            trans_no=nar.id,
                            total=nar.total
                        )
                        ojdt.save()

                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account,
                            credit=nar.total,
                            debit=0,
                            remarks="",
                            post_date=nar.posting_date,
                            customer=nar.code.id
                        )
                        arAcc = super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account
                        arAcc.balance -= nar.total
                        arAcc.save()

                        if super.round2(nar.vat) > 0:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account,
                                credit=0,
                                debit=nar.vat,
                                remarks="",
                                post_date=nar.posting_date,
                                customer=nar.code.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account
                            vat.balance -= nar.vat
                            vat.save()

                        for rows in ar1:
                            if int(rows.vatable) == 1:
                                si = super.round2(
                                    rows.amount) / Decimal("1.12")
                            else:
                                si = super.round2(rows.amount)
                            super.add_JE(
                                ojdt=ojdt,
                                account=rows.account,
                                credit=0,
                                debit=si,
                                remarks=rows.description,
                                post_date=nar.posting_date,
                                customer=rows.customer.id
                            )
                            acc = rows.account
                            acc.balance -= si
                            acc.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        old_inv = p_data.get("invoice")
        return Response({
            "success": True,
            "message": f"Invoice {old_inv} successfuly canceled."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_ar_cm(self, request):
        """
        <GET> /api/administration/add_ar_cm
        """
        data = request.data
        p_data = json.loads(data['datas'])
        p_rows = json.loads(data['rows'])
        p_wtax = json.loads(data['wtax'])
        # inv = p_data.get("invoice")
        # print(data)
        # print(super.round2(data.get("vatAmt")))
        # print(super.round2(data.get("discount")))
        print(p_data)
        print(p_rows)
        print(p_wtax)
        print(data['currId'])
        greater = "Document Total cannot be greater than the invoice balance."

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/R Credit Memo'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    # print("goods")
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Credit Memo Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/R Credit Memo Verifier"
                    )
                    bpartner = super.get_bp(id=p_data.get("cid")).first()
                    arinv = core_models.AROINV.objects.filter(
                        id=int(data['currId'])).first()
                    docTotal = super.round2(data.get("total"))
                    # print(f"1: {arinv.total}")
                    # print(f"2: {arinv.applied_amt}")
                    # print(f"3: {docTotal}")
                    if (arinv.total - (
                        arinv.applied_amt + arinv.applied_tax
                            )) < docTotal:
                        return Response({
                            "success": False,
                            "message": greater
                        }, status=status.HTTP_200_OK)

                    crm = core_models.AROCRM(
                        ar=arinv,
                        client=client,
                        code=bpartner,
                        bp_code=p_data.get("ccode"),
                        bp_name=p_data.get("cname"),
                        type=2,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        po_num=p_data.get("po"),
                        remarks=p_data.get("remarks"),
                        price_bef_vat=super.round2(data.get("tbda")),
                        discount=super.round2(data.get("discount")),
                        vat=super.round2(data.get("vatAmt")),
                        wtax=super.round2(data.get("wtaxAmt")),
                        total=docTotal,
                        added=request.user.user_acc.first()
                    )
                    if ver.status == 1:
                        crm.status = 5
                        end = "is awaiting your verification."
                        mess = f"A/R CM Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=3",
                            type=2
                        )
                    elif app.status == 1:
                        crm.status = 6
                        end = "is awaiting your approval."
                        mess = f"A/R CM Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=3",
                            type=2
                        )
                    else:
                        crm.status = 3
                    crm.save()

                    for rows in p_rows:
                        if rows.get("amount"):
                            crm1 = core_models.ARCRM1(
                                ar=crm,
                                description=rows.get("description"),
                                account=super.get_acc(
                                    int(rows.get("account"))),
                                customer=super.get_cust(
                                    int(rows.get("customer"))),
                                vatable=int(rows.get("vatable")),
                                wtax=int(rows.get("wtax")),
                                amount=super.round2(rows.get("amount"))
                            )
                            if rows.get("discount") != "":
                                crm1.discount = super.round2(
                                    rows.get("discount"))
                            crm1.save()

                    for rows in p_wtax:
                        if rows.get("code") != "0":
                            crm2 = core_models.ARCRM2(
                                ar=crm,
                                wtax=super.get_ae(id=int(rows.get("code"))),
                                name=rows.get("name"),
                                rate=super.get_ae(
                                    id=int(rows.get("code"))).rate,
                                taxable_amt=rows.get("tax_amt"),
                                wtax_amt=rows.get("wtax_amt")
                            )
                            crm2.save()

                    if ver.status == 2 and app.status == 2:
                        if (arinv.total - (
                            arinv.applied_amt + arinv.applied_tax
                                )) == docTotal:
                            arinv.status = 3
                            arinv.save()
                        # comment if implemented the cm on invoice
                        arinv.applied_amt = (
                            super.round2(arinv.applied_amt) +
                            super.round2(data.get("total")) -
                            super.round2(data.get("wtaxAmt")))
                        arinv.applied_tax = (
                            super.round2(arinv.applied_tax) +
                            super.round2(data.get("wtaxAmt")))
                        arinv.save()

                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=3,
                            origin_no=newInv,
                            remarks=f"Based on A/R Credit Memo {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=crm.id,
                            total=super.round2(data.get("total"))
                        )
                        ojdt.save()

                        total = super.round2(data.get("total"))
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account,
                            debit=abs(total) if total < 0 else 0,
                            credit=abs(total) if total > 0 else 0,
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=bpartner.id
                        )
                        ar = super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account
                        if (total > 0):
                            ar.balance -= total
                        else:
                            ar.balance += total
                        ar.save()

                        vatAmt = super.round2(data.get("vatAmt"))
                        if vatAmt != 0:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account,
                                debit=abs(vatAmt) if vatAmt > 0 else 0,
                                credit=abs(vatAmt) if vatAmt < 0 else 0,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=bpartner.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Output VAT"
                                ).account
                            if vatAmt > 0:
                                vat.balance -= vatAmt
                            else:
                                vat.balance += vatAmt
                            vat.save()

                        for rows in p_rows:
                            if rows.get("amount"):
                                ramt = super.round2(rows.get("amount"))
                                rdis = super.round2(rows.get("discount"))
                                vat = Decimal("1.12")
                                if int(rows.get("vatable")) == 1:
                                    si = (super.round2(ramt / vat) - rdis)
                                else:
                                    si = (ramt - rdis)
                                # amt = super.round2(rows.get("amount"))
                                super.add_JE(
                                    ojdt=ojdt,
                                    account=super.get_acc(
                                        int(rows.get("account"))),
                                    debit=abs(si) if si > 0 else 0,
                                    credit=abs(si) if si < 0 else 0,
                                    remarks=rows.get("description"),
                                    post_date=p_data.get("post_date"),
                                    customer=rows.get("customer")
                                )
                                acc = super.get_acc(int(rows.get("account")))
                                if si < 0:
                                    acc.balance += si
                                else:
                                    acc.balance -= si
                                acc.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Credit Memo successfuly added."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_invoices(self, request):
        """
        <GET> /api/administration/get_invoices
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")
        mod = request.query_params.get("mod")

        ac = core_models.AROINV.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            ac = ac.filter(
                Q(invoice_num__icontains=search) |
                Q(code__name__icontains=search)
            )
        if int(type) != 0:
            ac = ac.filter(
                code__id=int(type)
            )
        if dfrom and dto and int(fdate) != 0:
            ac = ac.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            ac = ac.filter(
                status=status1
            )
        if mod == "2":
            ac = ac.filter(
                status__in=[1, 2, 3]
            )

        ac = ac.order_by('-id')

        result_page = paginator.paginate_queryset(ac, request)
        serializer = u_ser.ARSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_invoice_preview(self, request):
        """
        <GET> /api/administration/id/get_invoice_preview
        """
        id = request.query_params.get("id")
        inv = core_models.AROINV.objects.filter(
            id=int(id)
        ).first()

        serializer = u_ser.InvSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_invoice_preview_ap(self, request):
        """
        <GET> /api/administration/id/get_invoice_preview_ap
        """
        id = request.query_params.get("id")
        inv = core_models.APOINV.objects.filter(
            id=id
        ).first()

        serializer = u_ser.InvAPSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_invoice_entry(self, request):
        """
        <GET> /api/administration/get_invoice_entry
        """
        origin = int(request.query_params.get("origin"))
        id = int(request.query_params.get("id"))
        type = int(request.query_params.get("type"))
        inv = core_models.OJDT.objects.filter(
            trans_no=id,
            origin=origin
        )
        if type == 2:
            inv = inv.order_by('-id').first()
        else:
            inv = inv.order_by('id').first()

        serializer = u_ser.JESerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_cm_invoices(self, request):
        """
        <GET> /api/administration/get_cm_invoices
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")

        ac = core_models.AROCRM.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            ac = ac.filter(
                Q(invoice_num__icontains=search) |
                Q(code__name__icontains=search)
            )
        if int(type) != 0:
            ac = ac.filter(
                code__id=int(type)
            )
        if dfrom and dto and int(fdate) != 0:
            ac = ac.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            ac = ac.filter(
                status=status1
            )

        ac = ac.order_by('-id')

        result_page = paginator.paginate_queryset(ac, request)
        serializer = u_ser.ARCMSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True)
    def get_cm_preview(self, request, pk):
        """
        <GET> /api/administration/id/get_cm_preview
        """
        inv = core_models.AROCRM.objects.filter(
            id=pk
        ).first()

        serializer = u_ser.CMSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_dashboard(self, request):
        """
        <GET> /api/administration/get_ar_dashboard
        """
        today = timezone.now().date()
        client = request.user.user_acc.first().client

        income = core_models.AROINV.objects.filter(
            client=client,
            status__in=[1, 2, 3],
            cancelation=False
        ).aggregate(
            # total=Sum(F('price_bef_vat') - F('discount'))
            # total=Sum(F('total') - F('discount'))
            total=Sum(F('total'))
        )['total'] or 0

        cm = core_models.AROCRM.objects.filter(
            client=client,
            status=3
        ).aggregate(
            # total=Sum(F('price_bef_vat') - F('discount'))
            # total=Sum(F('total') - F('discount'))
            total=Sum(F('total'))
        )['total'] or 0

        # overdue = core_models.AROINV.objects.filter(
        #     client=client,
        #     due_date__lt=today,
        #     status__in=[1, 2]
        # ).aggregate(
        #     total=Sum(F('price_bef_vat') - Coalesce(F('applied_amt'),
        #                                             Value(0.0)),
        #               output_field=DecimalField())
        # )['total'] or 0
        overdue = core_models.AROINV.objects.filter(
            client=client,
            receipt_date__lt=today,
            status__in=[1, 2]
            # ).annotate(
            #     cm_total=Coalesce(
            #         Sum('arcrm__total'),
            #         Value(0.0),
            #         output_field=DecimalField()
            #     )
        ).aggregate(
            total=Sum(F('total') -
                      Coalesce(F('applied_amt'), Value(0.0)) -
                      Coalesce(F('applied_tax'), Value(0.0)),
                      #   F('cm_total'),
                      output_field=DecimalField())
        )['total'] or 0

        # open = core_models.AROINV.objects.filter(
        #     client=client,
        #     status__in=[1, 2],
        #     cancelation=False
        # ).aggregate(
        #     total=Sum(
        #         F('price_bef_vat') - F('discount') - F('applied_amt') -
        #         F('applied_tax'), output_field=DecimalField())
        # )['total'] or 0
        open = core_models.AROINV.objects.filter(
            client=client,
            status__in=[1, 2],
            cancelation=False
        ).aggregate(
            total=Sum(
                F('total') - F('applied_amt') -
                F('applied_tax'), output_field=DecimalField())
        )['total'] or 0

        # .annotate(
        #     cm_total=Coalesce(
        #         Sum(F('arocrm__price_bef_vat') - F('arocrm__discount')),
        #         Value(0.0),
        #         output_field=DecimalField()
        #     )
        # )

        return Response({
            "success": True,
            "income": income - cm,
            # "inc": income,
            # "cm": cm,
            "overdue": overdue,
            "open": open
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ap_dashboard(self, request):
        """
        <GET> /api/administration/get_ap_dashboard
        """
        today = timezone.now().date()
        client = request.user.user_acc.first().client

        exp = core_models.APOINV.objects.filter(
            client=client,
            status__in=[1, 2, 3],
            cancelation=False
        ).aggregate(
            # total=Sum(F('price_bef_vat') - F('discount'))
            # total=Sum(F('total') - F('discount'))
            total=Sum(F('total'))
        )['total'] or 0

        cm = core_models.APOCRM.objects.filter(
            client=client,
            status=3
        ).aggregate(
            # total=Sum(F('price_bef_vat') - F('discount'))
            # total=Sum(F('total') - F('discount'))
            total=Sum(F('total'))
        )['total'] or 0

        overdue = core_models.APOINV.objects.filter(
            client=client,
            due_date__lt=today,
            status__in=[1, 2]
        )
        count_overdue = overdue.count()
        overdue_true = overdue.aggregate(
            total=Sum(F('total') -
                      Coalesce(F('applied_amt'), Value(0.0)) -
                      Coalesce(F('applied_tax'), Value(0.0)),
                      output_field=DecimalField())
        )['total'] or 0

        open = core_models.APOINV.objects.filter(
            client=client,
            status__in=[1, 2],
            cancelation=False
        )
        count_open = open.count()
        # open_true = open.annotate(
        #     cm_total=Coalesce(
        #         Sum(F('apocrm__price_bef_vat') - F('apocrm__discount')),
        #         Value(0.0),
        #         output_field=DecimalField()
        #     )
        # ).aggregate(
        #     total=Sum(F('price_bef_vat') - F('discount') - F('cm_total') -
        #               F('applied_amt'),
        #               output_field=DecimalField())
        # )['total'] or 0

        open_true = open.annotate(
            cm_total=Coalesce(
                Sum(
                    # F('apocrm__total') - F('apocrm__discount'),
                    F('apocrm__total'),
                    filter=Q(apocrm__status=3),
                    output_field=DecimalField()
                ),
                Value(0.0),
                output_field=DecimalField()
            )
        ).aggregate(
            total=Sum(F('total') - F('applied_tax') -
                      F('applied_amt'),
                      output_field=DecimalField())
        )['total'] or 0

        paid = core_models.OUTPAY1.objects.filter(
            out__client=client,
            # out__status=1
        ).aggregate(
            total=Sum(
                Case(
                    When(invoice__type=1, then=F('pay_bal')),
                    default=F('pay_bal') + F('pay_tax'),
                    output_field=DecimalField()
                )
            )
        )['total'] or 0

        ap_item = core_models.APOINV.objects.filter(
            client=client,
            status__in=[1, 2, 3],
            type=1,
            cancelation=False,
        ).aggregate(
            total=Sum(F('wtax'),
                      output_field=DecimalField())
        )['total'] or 0

        return Response({
            "success": True,
            "expense": exp - cm,
            # "exp": exp,
            # "cm": cm,
            "coverdue": count_overdue,
            "overdue": overdue_true,
            "copen": count_open,
            "open": open_true,
            "paid": paid + ap_item,
            "p1": paid,
            "p2": ap_item
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_recur(self, request, pk=None):
        """
        <GET> /api/administration/add_recur
        """
        data = request.data
        p_data = json.loads(data['datas'])
        type = int(data['type'])
        print(p_data)

        with transaction.atomic():
            if type == 1:
                getAR = core_models.AROINV.objects.filter(
                    id=int(p_data.get("template"))
                ).first()
                add_recur = core_models.RecTrans(
                    client=request.user.user_acc.first().client,
                    type=1,
                    ar=getAR,
                    name=p_data.get("name"),
                    period=int(p_data.get("rp")),
                    date=int(p_data.get("rd")),
                    sdate=p_data.get("sdate"),
                    valid=p_data.get("valid"),
                    created_by=request.user.user_acc.first(),
                )
                add_recur.save()
            else:
                getAP = core_models.APOINV.objects.filter(
                    id=int(p_data.get("template"))
                ).first()
                add_recur = core_models.RecTrans(
                    client=request.user.user_acc.first().client,
                    type=2,
                    ap=getAP,
                    name=p_data.get("name"),
                    period=int(p_data.get("rp")),
                    date=int(p_data.get("rd")),
                    sdate=p_data.get("sdate"),
                    valid=p_data.get("valid"),
                    created_by=request.user.user_acc.first(),
                )
                add_recur.save()

            for row in p_data.get("rows"):
                add_trans = core_models.RecDates(
                    rt=add_recur,
                    date=row['date'],
                )
                add_trans.save()

        return Response(
            {"success": True, "message": "Successfully Added."},
            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_recurring(self, request):
        """
        <GET> /api/administration/get_recurring
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        type1 = request.query_params.get("type1")
        # client = request.query_params.get("from")
        # dto = request.query_params.get("to")
        # fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")

        ac = core_models.RecTrans.objects.filter(
            client=request.user.user_acc.first().client,
            type=int(type)
        )
        if int(type) == 1:
            if search:
                ac = ac.filter(
                    Q(ar__invoice_num__icontains=search) |
                    Q(ar__code__name__icontains=search)
                )

            if int(type1) != 0:
                ac = ac.filter(
                    ar__code__id=type1
                )

            if int(status1) != 0:
                ac = ac.filter(
                    status=status1
                )
        else:
            if search:
                ac = ac.filter(
                    Q(ap__invoice_num__icontains=search) |
                    Q(ap__code__name__icontains=search)
                )

            if int(type1) != 0:
                ac = ac.filter(
                    ap__code__id=type1
                )

            if int(status1) != 0:
                ac = ac.filter(
                    status=status1
                )

        ac = ac.order_by('-id')

        result_page = paginator.paginate_queryset(ac, request)
        serializer = u_ser.RecurringSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['PUT'], detail=False)
    def up_recur(self, request, pk=None):
        """
        <GET> /api/administration/up_recur
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        with transaction.atomic():
            query = core_models.RecTrans.objects.filter(
                id=int(p_data.get("id"))
            ).first()
            if int(p_data.get("status")) == 2:
                query.status = 2
                query.save()

                trans = core_models.RecDates.objects.filter(
                    rt=query
                )
                for tran in trans:
                    tran.status = 2
                    tran.save()

        return Response(
            {"success": True, "message": "Successfully updated."},
            status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_ap_invoice(self, request):
        """
        <GET> /api/administration/add_ap_invoice
        """
        data = request.data
        p_data = json.loads(data['datas'])
        p_rows = json.loads(data['rows'])
        p_wtax = json.loads(data['wtax'])
        docType = int(data.get("docType"))
        # inv = p_data.get("invoice")
        # print(data)
        # print(super.round2(data.get("vatAmt")))
        # print(super.round2(data.get("discount")))
        print(p_wtax)

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/P Invoice'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    # print("goods")
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Verifier"
                    )
                    bpartner = super.get_bp(id=p_data.get("cid")).first()
                    print(f"Rounded {super.round2(data.get('wtaxAmt'))}")
                    print(f"Not Rounded {data.get('wtaxAmt')}")
                    ar = core_models.APOINV(
                        client=client,
                        code=bpartner,
                        bp_code=p_data.get("ccode"),
                        bp_name=p_data.get("cname"),
                        type=docType,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        po_num=p_data.get("po"),
                        remarks=p_data.get("remarks"),
                        price_bef_vat=super.round2(data.get("tbda")),
                        discount=super.round2(data.get("discount")),
                        vat=super.round2(data.get("vatAmt")),
                        wtax=super.round2(data.get("wtaxAmt")),
                        total=super.round2(data.get("total")),
                        added=request.user.user_acc.first()
                    )
                    if docType == 1:
                        ar.applied_tax = super.round2(data.get("wtaxAmt"))
                    if ver.status == 1:
                        ar.status = 5
                        end = "is awaiting your verification."
                        mess = f"A/P Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=4",
                            type=2
                        )
                    elif app.status == 1:
                        ar.status = 6
                        end = "is awaiting your approval."
                        mess = f"A/P Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=4",
                            type=2
                        )
                    else:
                        ar.status = 1
                    ar.save()

                    for rows in p_rows:
                        if rows.get("amount"):
                            ar1 = core_models.APINV1(
                                ap=ar,
                                vatable=int(rows.get("vatable")),
                                wtax=int(rows.get("wtax")),
                                amount=super.round2(rows.get("amount"))
                            )
                            if docType == 2:
                                ar1.description = rows.get("description")
                                ar1.account = super.get_acc(
                                    int(rows.get("account")))
                            else:
                                prod = super.get_prod(int(rows.get("product")))
                                ar1.description = prod.name
                                ar1.account = super.get_ae(
                                    client=client,
                                    type="Inventory Account"
                                ).account
                                ar1.product = prod
                                ar1.price = super.round2(rows.get("price"))
                                ar1.qty = super.round2(rows.get("qty"))

                            if rows.get("customer"):
                                ar1.customer = super.get_cust(
                                    int(rows.get("customer")))
                            if rows.get("discount") != "":
                                ar1.discount = super.round2(
                                    rows.get("discount"))
                            ar1.save()

                    for rows in p_wtax:
                        if rows.get("code") != "0":
                            ar2 = core_models.APINV2(
                                ap=ar,
                                wtax=super.get_ae(id=int(rows.get("code"))),
                                name=rows.get("name"),
                                rate=super.get_ae(
                                    id=int(rows.get("code"))).rate,
                                taxable_amt=rows.get("tax_amt"),
                                wtax_amt=rows.get("wtax_amt")
                            )
                            ar2.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=4,
                            origin_no=newInv,
                            remarks=f"Based on A/P Invoice {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=ar.id,
                            total=super.round2(data.get("total"))
                        )
                        ojdt.save()

                        if docType == 1:
                            ap_amt = (
                                super.round2(data.get("total")) -
                                super.round2(data.get("wtaxAmt"))
                            )
                        else:
                            ap_amt = super.round2(data.get("total"))
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=0,
                            credit=ap_amt,
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=bpartner.id
                        )
                        ar = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        ar.balance += ap_amt
                        ar.save()

                        for rows in p_rows:
                            ramt = super.round2(rows.get("amount"))
                            rdis = super.round2(rows.get("discount"))
                            vat = Decimal("1.12")
                            if int(rows.get("vatable")) == 1:
                                ap = (super.round2(ramt / vat) - rdis)
                            else:
                                ap = (ramt - rdis)
                            # if int(rows.get("vatable")) == 1:
                            #     ap = (super.round2(
                            #         rows.get("amount")) / Decimal(1.12) -
                            #         super.round2(rows.get("discount")))
                            # else:
                            #     ap = (super.round2(rows.get("amount")) -
                            #           super.round2(rows.get("discount")))
                            if rows.get("amount"):
                                if docType == 2:
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=super.get_acc(
                                            int(rows.get("account"))),
                                        debit=ap,
                                        credit=0,
                                        remarks=rows.get("description"),
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    acc = super.get_acc(
                                        int(rows.get("account")))
                                    acc.balance += ap
                                    acc.save()
                                else:
                                    ia = super.get_ae(
                                        client=client,
                                        type="Inventory Account"
                                    )
                                    if not ia.account:
                                        m1 = "Please select"
                                        mes = f"{m1} Inventory Account."
                                        raise PermissionDenied(mes)
                                    prod = super.get_prod(
                                        int(rows.get("product")))
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=ia.account,
                                        debit=ap,
                                        credit=0,
                                        remarks=rows.get("description"),
                                        post_date=p_data.get("post_date"),
                                        customer=rows.get("customer")
                                    )
                                    acc = ia.account
                                    acc.balance += ap
                                    acc.save()
                                    upQty = core_models.Inventory.objects.get(
                                        id=prod.id
                                    )
                                    upQty.stock += super.round2(
                                        rows.get("qty"))
                                    upQty.save()

                        if super.round2(data.get("vatAmt")) > 0:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account,
                                debit=super.round2(data.get("vatAmt")),
                                credit=0,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=bpartner.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account
                            vat.balance += super.round2(data.get("vatAmt"))
                            vat.save()

                        if docType == 1:
                            for rows in p_wtax:
                                if rows.get("code") != "0":
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=super.get_ae(
                                            id=int(rows.get("code"))).account,
                                        debit=0,
                                        credit=rows.get("wtax_amt"),
                                        remarks=super.get_ae(
                                            id=int(rows.get("code"))).type,
                                        post_date=p_data.get("post_date"),
                                        customer=""
                                    )
                                    acc1 = super.get_ae(
                                        id=int(rows.get("code"))).account
                                    print(f"ACC1 {acc1}")
                                    acc1.balance += Decimal(
                                        rows.get("wtax_amt"))
                                    acc1.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": f"Invoice {newInv} successfuly added."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def cancel_ap_invoice(self, request):
        """
        <GET> /api/administration/cancel_ap_invoice
        """
        data = request.data
        p_data = json.loads(data['datas'])
        id = int(data['currId'])

        ar = core_models.APOINV.objects.filter(id=id).first()

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/P Invoice - Cancelation'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Verifier"
                    )

                    rem = ar.remarks
                    old_inv = p_data.get("invoice")
                    remarks = f"{rem} Cancellation of Invoice No. {old_inv}."
                    nar = core_models.APOINV(
                        client=client,
                        code=ar.code,
                        bp_code=ar.bp_code,
                        bp_name=ar.bp_name,
                        type=ar.type,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=ar.due_date,
                        doc_date=ar.doc_date,
                        po_num=ar.po_num,
                        remarks=remarks,
                        price_bef_vat=ar.price_bef_vat,
                        discount=ar.discount,
                        vat=ar.vat,
                        wtax=ar.wtax,
                        total=ar.total,
                        cancelation=True,
                        canceledAP=ar,
                        added=ar.added
                    )
                    if ver.status == 1:
                        nar.status = 5
                    elif app.status == 1:
                        nar.status = 6
                    else:
                        nar.status = 3
                        ar.status = 4
                    ar.save()
                    nar.save()

                    ar1 = core_models.APINV1.objects.filter(ap=ar)
                    for rows in ar1:
                        nar1 = core_models.APINV1(
                            ap=nar,
                            description=rows.description,
                            account=rows.account,
                            customer=rows.customer,
                            vatable=rows.vatable,
                            wtax=rows.wtax,
                            amount=rows.amount,
                            discount=rows.discount,
                            qty=rows.qty,
                            price=rows.price,
                            product=rows.product
                        )
                        nar1.save()

                    ar2 = core_models.APINV2.objects.filter(ap=ar)
                    for rows in ar2:
                        nar2 = core_models.APINV2(
                            ap=nar,
                            wtax=rows.wtax,
                            name=rows.name,
                            rate=rows.rate,
                            taxable_amt=rows.taxable_amt,
                            wtax_amt=rows.wtax_amt
                        )
                        nar2.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=4,
                            origin_no=newInv,
                            remarks=f"Based on A/R Invoice {newInv}",
                            post_date=nar.posting_date,
                            due_date=nar.due_date,
                            doc_date=nar.doc_date,
                            trans_no=nar.id,
                            total=nar.total
                        )
                        ojdt.save()

                        t_debit = 0
                        if ar.type == 1:
                            t_debit = nar.total - nar.wtax
                        else:
                            t_debit = nar.total
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=t_debit,
                            credit=0,
                            remarks="",
                            post_date=nar.posting_date,
                            customer=nar.code.id
                        )
                        arAcc = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        arAcc.balance -= nar.total
                        arAcc.save()

                        if super.round2(nar.vat) > 0:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account,
                                debit=0,
                                credit=nar.vat,
                                remarks="",
                                post_date=nar.posting_date,
                                customer=nar.code.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account
                            vat.balance -= nar.vat
                            vat.save()

                        for rows in ar1:
                            if int(rows.vatable) == 1:
                                si = super.round2(
                                    rows.amount) / Decimal("1.12")
                            else:
                                si = super.round2(rows.amount)
                            super.add_JE(
                                ojdt=ojdt,
                                account=rows.account,
                                debit=0,
                                credit=si,
                                remarks=rows.description,
                                post_date=nar.posting_date,
                                customer=rows.customer.id
                            )
                            acc = rows.account
                            acc.balance -= si
                            acc.save()

                        if ar.type == 1:
                            for rows in ar2:
                                super.add_JE(
                                    ojdt=ojdt,
                                    account=rows.wtax.account,
                                    debit=rows.wtax_amt,
                                    credit=0,
                                    remarks=rows.wtax.type,
                                    post_date=nar.posting_date,
                                    customer=""
                                )
                                acc = rows.wtax.account
                                acc.balance -= rows.wtax_amt
                                acc.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        old_inv = p_data.get("invoice")
        return Response({
            "success": True,
            "message": f"Invoice {old_inv} successfuly canceled."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_ap_cm(self, request):
        """
        <GET> /api/administration/add_ap_cm
        """
        data = request.data
        p_data = json.loads(data['datas'])
        p_rows = json.loads(data['rows'])
        p_wtax = json.loads(data['wtax'])
        print(p_data)
        print(p_rows)
        print(f"P_Wtax {p_wtax}")
        print(data['currId'])
        greater = "Document Total cannot be greater than the invoice balance."

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            docNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='A/P Credit Memo'
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Credit Memo Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="A/P Credit Memo Verifier"
                    )
                    bpartner = super.get_bp(id=p_data.get("cid")).first()
                    arinv = core_models.APOINV.objects.filter(
                        id=int(data['currId'])).first()
                    docTotal = super.round2(data.get("total"))
                    if (arinv.total - (arinv.applied_amt or 0)) < docTotal:
                        return Response({
                            "success": False,
                            "message": greater
                        }, status=status.HTTP_200_OK)

                    crm = core_models.APOCRM(
                        ap=arinv,
                        client=client,
                        code=bpartner,
                        bp_code=p_data.get("ccode"),
                        bp_name=p_data.get("cname"),
                        type=2,
                        invoice_num=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        po_num=p_data.get("po"),
                        remarks=p_data.get("remarks"),
                        price_bef_vat=super.round2(data.get("tbda")),
                        discount=super.round2(data.get("discount")),
                        vat=super.round2(data.get("vatAmt")),
                        wtax=super.round2(data.get("wtaxAmt")),
                        total=docTotal,
                        added=request.user.user_acc.first()
                    )
                    if ver.status == 1:
                        crm.status = 5
                        end = "is awaiting your verification."
                        mess = f"A/P CM Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=5",
                            type=2
                        )
                    elif app.status == 1:
                        crm.status = 6
                        end = "is awaiting your approval."
                        mess = f"A/P CM Invoice {newInv} {end}"
                        super.add_notif(
                            client=client,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=5",
                            type=2
                        )
                    else:
                        crm.status = 3
                    crm.save()

                    for rows in p_rows:
                        if rows.get("amount"):
                            crm1 = core_models.APCRM1(
                                ap=crm,
                                description=rows.get("description"),
                                account=super.get_acc(
                                    int(rows.get("account"))),
                                vatable=int(rows.get("vatable")),
                                wtax=int(rows.get("wtax")),
                                amount=super.round2(rows.get("amount"))
                            )
                            if rows.get("customer"):
                                crm1.customer = super.get_cust(
                                    int(rows.get("customer")))
                            if rows.get("discount") != "":
                                crm1.discount = super.round2(
                                    rows.get("discount"))
                            crm1.save()

                    for rows in p_wtax:
                        if rows.get("code"):
                            crm2 = core_models.APCRM2(
                                ap=crm,
                                wtax=super.get_ae(id=int(rows.get("code"))),
                                name=rows.get("name"),
                                rate=super.get_ae(
                                    id=int(rows.get("code"))).rate,
                                taxable_amt=rows.get("tax_amt"),
                                wtax_amt=rows.get("wtax_amt")
                            )
                            crm2.save()

                    if ver.status == 2 and app.status == 2:
                        total1 = arinv.total - (arinv.applied_amt or 0)
                        if total1 == docTotal:
                            arinv.status = 3
                            arinv.save()

                        arinv.applied_amt = (
                            super.round2(arinv.applied_amt) +
                            super.round2(data.get("total")) -
                            super.round2(data.get("wtaxAmt")))
                        arinv.applied_tax = (
                            super.round2(arinv.applied_tax) +
                            super.round2(data.get("wtaxAmt")))
                        arinv.save()

                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=5,
                            origin_no=newInv,
                            remarks=f"Based on A/P Credit Memo {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=crm.id,
                            total=super.round2(data.get("total"))
                        )
                        ojdt.save()

                        # ap_amt = (
                        #     super.round2(data.get("total")) -
                        #     super.round2(data.get("wtaxAmt"))
                        # )
                        # total = super.round2(data.get("total"))
                        ap_amt = super.round2(data.get("total"))
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=abs(ap_amt) if ap_amt > 0 else 0,
                            credit=abs(ap_amt) if ap_amt < 0 else 0,
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=bpartner.id
                        )
                        ar = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        if (ap_amt > 0):
                            ar.balance -= ap_amt
                        else:
                            ar.balance += ap_amt
                        ar.save()

                        for rows in p_rows:
                            ramt = super.round2(rows.get("amount"))
                            rdis = super.round2(rows.get("discount"))
                            vat = Decimal("1.12")
                            # if int(rows.get("vatable")) == 1:
                            #     ap = (super.round2(
                            #         rows.get("amount")) / Decimal(1.12) -
                            #         super.round2(rows.get("discount")))
                            # else:
                            #     ap = (super.round2(rows.get("amount")) -
                            #           super.round2(rows.get("discount")))
                            if rows.get("amount"):
                                if int(rows.get("vatable")) == 1:
                                    ap = (super.round2(ramt / vat) - rdis)
                                else:
                                    ap = (ramt - rdis)
                                # amt = super.round2(rows.get("amount"))
                                super.add_JE(
                                    ojdt=ojdt,
                                    account=super.get_acc(
                                        int(rows.get("account"))),
                                    debit=abs(ap) if ap < 0 else 0,
                                    credit=abs(ap) if ap > 0 else 0,
                                    remarks=rows.get("description"),
                                    post_date=p_data.get("post_date"),
                                    customer=rows.get("customer")
                                )
                                acc = super.get_acc(int(rows.get("account")))
                                if ap < 0:
                                    acc.balance += ap
                                else:
                                    acc.balance -= ap
                                acc.save()

                        vatAmt = super.round2(data.get("vatAmt"))
                        if vatAmt != 0:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account,
                                debit=abs(vatAmt) if vatAmt < 0 else 0,
                                credit=abs(vatAmt) if vatAmt > 0 else 0,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=bpartner.id
                            )
                            vat = super.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account
                            if vatAmt > 0:
                                vat.balance -= vatAmt
                            else:
                                vat.balance += vatAmt
                            vat.save()

                        # for rows in p_wtax:
                        for index, rows in enumerate(p_wtax):
                            if rows.get("code"):
                                wtaxAmt = super.round2(rows.get("wtax_amt"))
                                # super.add_JE(
                                #     ojdt=ojdt,
                                #     account=super.get_ae(
                                #         id=int(rows.get("code"))).account,
                                #     debit=abs(wtaxAmt) if wtaxAmt > 0 else 0,
                                #  credit=abs(wtaxAmt) if wtaxAmt < 0 else 0,
                                #     remarks=super.get_ae(
                                #         id=int(rows.get("code"))).type,
                                #     post_date=p_data.get("post_date"),
                                #     customer=""
                                # )
                                # acc1 = super.get_ae(
                                #     id=int(rows.get("code"))).account
                                # if wtaxAmt > 0:
                                #     acc1.balance -= wtaxAmt
                                # else:
                                #     acc1.balance += wtaxAmt
                                # acc1.save()

                                tax_row = arinv.invAPTax.all()[index]
                                if tax_row.paid:
                                    tax_row.paid += wtaxAmt
                                else:
                                    tax_row.paid = wtaxAmt
                                tax_row.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Credit Memo successfuly added."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ap_invoices(self, request):
        """
        <GET> /api/administration/get_ap_invoices
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")
        mod = request.query_params.get("mod")

        ac = core_models.APOINV.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            ac = ac.filter(
                invoice_num__icontains=search
            )
        if int(type) != 0:
            ac = ac.filter(
                code__id=int(type)
            )
        if dfrom and dto and int(fdate) != 0:
            ac = ac.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            ac = ac.filter(
                status=status1
            )
        if int(mod) == 2:
            ac = ac.filter(
                status__in=[1, 2, 3]
            )
        ac = ac.order_by('-id')

        result_page = paginator.paginate_queryset(ac, request)
        serializer = u_ser.APSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_cm_ap_invoices(self, request):
        """
        <GET> /api/administration/get_cm_ap_invoices
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")

        ac = core_models.APOCRM.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            ac = ac.filter(
                Q(invoice_num__icontains=search) |
                Q(code__name__icontains=search)
            )
        if int(type) != 0:
            ac = ac.filter(
                code__id=int(type)
            )
        if dfrom and dto and int(fdate) != 0:
            ac = ac.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            ac = ac.filter(
                status=status1
            )

        ac = ac.order_by('-id')

        result_page = paginator.paginate_queryset(ac, request)
        serializer = u_ser.APCMSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True)
    def get_cm_ap_preview(self, request, pk):
        """
        <GET> /api/administration/id/get_cm_ap_preview
        """
        inv = core_models.APOCRM.objects.filter(
            id=pk
        ).first()

        serializer = u_ser.CMAPSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_rec_trans(self, request):
        """
        <GET> /api/administration/get_rec_trans
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        id = request.query_params.get("id")

        query = core_models.RecDates.objects.filter(
            rt__id=int(id)
        ).order_by('id')

        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.RecTransSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_incoming_invoices(self, request):
        """
        <GET> /api/administration/get_incoming_invoices
        """
        id = request.query_params.get("id")
        inv = core_models.AROINV.objects.filter(
            code__id=id,
            status__in=[1, 2]
        ).order_by('-id')

        serializer = u_ser.IncomingInvoicesSerializer(inv, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_outgoing_invoices(self, request):
        """
        <GET> /api/administration/get_outgoing_invoices
        """
        id = request.query_params.get("id")
        inv = core_models.APOINV.objects.filter(
            code__id=id,
            status__in=[1, 2]
        ).order_by('-id')

        serializer = u_ser.OutgoingInvoicesSerializer(inv, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_incoming(self, request):
        """
        <GET> /api/administration/add_incoming
        """
        data = request.data
        p_data = json.loads(data['datas'])
        rows = json.loads(data['rows'])
        type = int(data['type'])
        print(data['type'])
        print(p_data)
        print(rows)

        post = core_models.PostingPeriod.objects.filter(
            from_date__lte=p_data.get("post_date"),
            to_date__gte=p_data.get("post_date")
        ).first()
        docNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client,
            name='Incoming Payment'
        ).first()
        jeNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client,
            name='Journal Entry'
        ).first()
        cli = request.user.user_acc.first().client
        newInv = int(docNo.no) + 1
        newJE = int(jeNo.no) + 1
        with transaction.atomic():
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    app = core_models.Approval.objects.get(
                        client=cli,
                        module="Incoming Payment Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=cli,
                        module="Incoming Payment Verifier"
                    )
                    print(super.get_bp(id=p_data.get("bpid")).first())
                    inc = core_models.INCPAY(
                        client=cli,
                        type=int(type),
                        doc_no=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        or_num=p_data.get("or"),
                        remarks=p_data.get("remarks"),
                        payment_account=super.round2(p_data.get("poa")),
                        total_amt=super.round2(p_data.get("paid")),
                        added=request.user.user_acc.first()
                    )
                    if type == 1 or type == 2:
                        inc.code = super.get_bp(
                            id=p_data.get("bpid")).first()
                        inc.bp_code = p_data.get("bpcode")
                        inc.bp_name = p_data.get("bpname")
                    if ver.status == 1:
                        inc.status = 3
                        end = "is awaiting your verification."
                        mess = f"Incoming Payment {newInv} {end}"
                        super.add_notif(
                            client=cli,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=6",
                            type=2
                        )
                    elif app.status == 1:
                        inc.status = 4
                        end = "is awaiting your approval."
                        mess = f"Incoming Payment {newInv} {end}"
                        super.add_notif(
                            client=cli,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=6",
                            type=2
                        )
                    else:
                        inc.status = 6
                    inc.save()

                    inc2 = core_models.INCPAY2(
                        inc=inc,
                        type=int(p_data.get('p_type')),
                        account=super.get_acc(int(p_data.get('bank_id'))),
                        check_no=p_data.get('check_no'),
                        reference=p_data.get('reference'),
                    )
                    if p_data.get('transfer_date'):
                        inc2.transfer_date = p_data.get('transfer_date')
                    inc2.save()

                    if type == 1:
                        for inv in p_data.get('invoices'):
                            inv_tax = super.round2(inv['wtax'])
                            inv_tot = super.round2(inv['total'])
                            inv_true = inv_tot - inv_tax
                            rate = super.round2(inv['payment']) / inv_true
                            invoice = core_models.AROINV.objects.filter(
                                id=inv['id']
                            ).first()
                            # print(f"Inv Payment {inv['payment']}")
                            # print(f"inv_true {inv_true}")
                            # print(f"Rate: {rate}")
                            true_tax = 0
                            for iTax in invoice.invTax.all():
                                paid = super.round2(iTax.paid)
                                true_tax += ((iTax.wtax_amt - paid) * rate)
                            # print(f"True Tax {super.round2(true_tax)}")

                            inc1 = core_models.INCPAY1(
                                inc=inc,
                                invoice=invoice,
                                amount=super.round2(inv['total']) -
                                super.round2(inv['wtax']),
                                wtax=super.round2(inv['wtax']),
                                pay_bal=super.round2(inv['payment']),
                                pay_tax=true_tax,
                            )
                            inc1.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=cli,
                            no=newJE,
                            origin=6,
                            origin_no=newInv,
                            remarks=f"Based on Incoming Payment {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=inc.id,
                            total=super.round2(p_data.get("paid"))
                        )
                        ojdt.save()

                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_acc(int(p_data.get('bank_id'))),
                            debit=super.round2(p_data.get("paid")),
                            credit=0,
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=p_data.get("bpid")
                        )
                        deb = super.get_acc(int(p_data.get('bank_id')))
                        deb.balance += super.round2(p_data.get("paid"))
                        deb.save()

                        if type == 1:
                            total_payment = 0
                            for inv in p_data.get('invoices'):
                                inv_tax = super.round2(inv['wtax'])
                                inv_tot = super.round2(inv['total'])
                                inv_true = inv_tot - inv_tax
                                # total_payment += (
                                #     super.round2(inv['payment']) +
                                #     (inv_tax * rate)
                                # )
                                invoice = core_models.AROINV.objects.filter(
                                    id=inv['id']
                                ).first()

                                inv2 = core_models.ARINV2.objects.filter(
                                    ar=invoice
                                )
                                total_tax = 0
                                if inv2:
                                    for in2 in inv2:
                                        print(f"WTAX INV {in2.wtax_amt}")
                                        print(f"rate INV {rate}")
                                        paid = super.round2(in2.paid)
                                        rate = (
                                            super.round2(inv['payment']) /
                                            super.round2(inv['balance'])
                                        )
                                        tax_amt = (in2.wtax_amt - paid) * rate
                                        total_tax += super.round2(tax_amt)
                                        total_payment += super.round2(tax_amt)

                                        print(f"Rate: {rate}")
                                        print(f"Tax: {super.round2(tax_amt)}")
                                        super.add_JE(
                                            ojdt=ojdt,
                                            account=in2.wtax.account,
                                            debit=super.round2(tax_amt),
                                            credit=0,
                                            remarks="",
                                            post_date=p_data.get("post_date"),
                                            customer=p_data.get("bpid")
                                        )
                                        up_ac = in2.wtax.account
                                        up_ac.balance += super.round2(tax_amt)
                                        up_ac.save()

                                        in2.paid = (
                                            super.round2(in2.paid) +
                                            super.round2(tax_amt)
                                        )
                                        in2.save()

                                print(f"inv_tax - {inv_tax}")
                                print(f"inv_tot - {inv_tot}")
                                print(f"inv_true - {inv_true}")
                                print(f"rate - {rate}")

                                if inv_true == super.round2(inv['payment']):
                                    print("Same")
                                    invoice.status = 3
                                    invoice.applied_tax = invoice.wtax
                                    print(f"Full Payment {invoice.wtax}")
                                else:
                                    invoice.status = 2
                                    invoice.applied_tax += total_tax
                                    print(f"Partial Payment {total_tax}")
                                apl = super.round2(invoice.applied_amt)
                                pay = super.round2(inv['payment'])
                                invoice.applied_amt = apl + pay
                                invoice.save()

                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=cli,
                                    type="A/R Account"
                                ).account,
                                debit=0,
                                credit=(
                                    total_payment +
                                    super.round2(p_data.get("paid"))
                                ),
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=p_data.get("bpid")
                            )
                            cre = super.get_ae(
                                    client=cli,
                                    type="A/R Account"
                                ).account
                            cre.balance -= (
                                total_payment +
                                super.round2(p_data.get("paid"))
                            )
                            cre.save()
                            print(f"Payment: {super.round2(inv['payment'])}")
                            print(f"Tax: {inv_tax * rate}")

                        elif type == 2:
                            print(2)
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=cli,
                                    type="A/P Account"
                                ).account,
                                debit=0,
                                credit=super.round2(p_data.get("paid")),
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=p_data.get("bpid")
                            )
                            cre = super.get_ae(
                                    client=cli,
                                    type="A/P Account"
                                ).account
                            cre.balance -= super.round2(p_data.get("paid"))
                            cre.save()

                        elif type == 3:
                            print(3)
                            for ro in rows:
                                if ro['code'] != "":
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=super.get_acc(int(ro['code'])),
                                        debit=0,
                                        credit=super.round2(ro['amount']),
                                        remarks="",
                                        post_date=p_data.get("post_date"),
                                        customer=ro['customer']
                                    )
                                    cre = super.get_acc(int(ro['code']))
                                    cre.balance -= super.round2(ro['amount'])
                                    cre.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Successfully Added."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_incoming_trans(self, request):
        """
        <GET> /api/administration/get_incoming_trans
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")
        bp = request.query_params.get("bp")
        bank = request.query_params.get("bank")

        inv = core_models.INCPAY.objects.filter(
            client=request.user.user_acc.first().client
        )
        if search:
            inv = inv.filter(
                or_num__icontains=search
            )
        if int(bp) != 0:
            if int(type) != 0:
                inv = inv.filter(
                    code__id=int(type)
                )
            else:
                inv = inv.filter(
                    code__type=int(bp)
                )
        if int(bank) != 0:
            inv = inv.filter(
               incBank__account__id=int(bank)
            )
        if dfrom and dto and int(fdate) != 0:
            inv = inv.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            inv = inv.filter(
                status=status1
            )

        inv = inv.order_by('-id')

        result_page = paginator.paginate_queryset(inv, request)
        serializer = u_ser.IncomingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_incoming_trans1(self, request):
        """
        <GET> /api/administration/get_incoming_trans1
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        bank = int(request.query_params.get("bank"))

        inv = core_models.INCPAY.objects.filter(
            client=request.user.user_acc.first().client,
            reconciled=False,
            incBank__account__id=bank,
            status=6
        ).order_by('-id')

        result_page = paginator.paginate_queryset(inv, request)
        serializer = u_ser.IncomingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_transaction_preview(self, request):
        """
        <GET> /api/administration/id/get_transaction_preview
        """
        id = request.query_params.get("id")
        inv = core_models.INCPAY.objects.filter(
            id=int(id)
        ).first()

        serializer = u_ser.IncSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def get_check_no(self, request, pk):
        """
        <GET> /api/administration/id/get_check_no
        """
        que = core_models.Accounts.objects.filter(
            id=pk
        ).first()

        no = 0
        if que:
            no = 0 if que.check_no is None else que.check_no

        return Response({
            "success": True,
            "no": no
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_outgoing(self, request):
        """
        <GET> /api/administration/add_outgoing
        """
        data = request.data
        p_data = json.loads(data['datas'])
        rows = json.loads(data['rows'])
        type = int(data['type'])
        print(data['type'])
        print(p_data)
        print(rows)

        post = core_models.PostingPeriod.objects.filter(
            from_date__lte=p_data.get("post_date"),
            to_date__gte=p_data.get("post_date")
        ).first()
        docNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client,
            name='Outgoing Payment'
        ).first()
        jeNo = core_models.DocumentNo.objects.filter(
            client=request.user.user_acc.first().client,
            name='Journal Entry'
        ).first()
        cli = request.user.user_acc.first().client
        newInv = int(docNo.no) + 1
        newJE = int(jeNo.no) + 1
        with transaction.atomic():
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    app = core_models.Approval.objects.get(
                        client=cli,
                        module="Outgoing Payment Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=cli,
                        module="Outgoing Payment Verifier"
                    )
                    print(super.get_bp(id=p_data.get("bpid")).first())
                    inc = core_models.OUTPAY(
                        client=cli,
                        type=int(type),
                        doc_no=newInv,
                        posting_date=p_data.get("post_date"),
                        due_date=p_data.get("due_date"),
                        doc_date=p_data.get("doc_date"),
                        or_num=p_data.get("or"),
                        remarks=p_data.get("remarks"),
                        payment_account=super.round2(p_data.get("poa")),
                        total_amt=super.round2(p_data.get("paid")),
                        added=request.user.user_acc.first()
                    )
                    if type == 1 or type == 2:
                        inc.code = super.get_bp(
                            id=p_data.get("bpid")).first()
                        inc.bp_code = p_data.get("bpcode")
                        inc.bp_name = p_data.get("bpname")
                    if ver.status == 1:
                        inc.status = 3
                        modul = "Outgoing Payment"
                        end = "is awaiting your verification."
                        mess = f"{modul} {newInv} {end}"
                        super.add_notif(
                            client=cli,
                            sender=request.user.user_acc.first(),
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=7",
                            type=2
                        )
                    elif app.status == 1:
                        inc.status = 4
                        modul = "Outgoing Payment"
                        mess = f"{modul} {newInv} is awaiting your approval."
                        super.add_notif(
                            client=cli,
                            sender=request.user.user_acc.first(),
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=7",
                            type=2
                        )
                    else:
                        inc.status = 6
                    inc.save()

                    inc2 = core_models.OUTPAY2(
                        out=inc,
                        type=int(p_data.get('p_type')),
                        account=super.get_acc(int(p_data.get('bank_id'))),
                        check_no=p_data.get('check_no'),
                        reference=p_data.get('reference'),
                    )
                    if p_data.get('transfer_date'):
                        inc2.transfer_date = p_data.get('transfer_date')
                    inc2.save()

                    if type == 2:
                        for inv in p_data.get('invoices'):
                            invoice = core_models.APOINV.objects.filter(
                                id=inv['id']
                            ).first()
                            inv_tax = super.round2(inv['wtax'])
                            inv_tot = super.round2(inv['total'])
                            inv_true = inv_tot - inv_tax
                            rate = super.round2(inv['payment']) / inv_true
                            print(f"Rate: {rate}")

                            true_tax = 0
                            for iTax in invoice.invAPTax.all():
                                paid = super.round2(iTax.paid)
                                true_tax += ((iTax.wtax_amt - paid) * rate)
                            # true_tax = super.round2(inv['wtax']) * rate

                            print(f"inv_tax - {inv_tax}")
                            print(f"inv_tot - {inv_tot}")
                            print(f"inv_true - {inv_true}")
                            print(f"rate - {rate}")

                            inc1 = core_models.OUTPAY1(
                                out=inc,
                                invoice=invoice,
                                amount=super.round2(inv['total']) -
                                super.round2(inv['wtax']),
                                wtax=super.round2(inv['wtax']),
                                pay_bal=super.round2(inv['payment']),
                                pay_tax=true_tax,
                            )
                            inc1.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=cli,
                            no=newJE,
                            origin=7,
                            origin_no=newInv,
                            remarks=f"Based on Outgoing Payment {newInv}",
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=inc.id,
                            total=super.round2(p_data.get("paid"))
                        )
                        ojdt.save()

                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_acc(int(p_data.get('bank_id'))),
                            debit=0,
                            credit=super.round2(p_data.get("paid")),
                            remarks="",
                            post_date=p_data.get("post_date"),
                            customer=p_data.get("bpid")
                        )
                        deb = super.get_acc(int(p_data.get('bank_id')))
                        deb.balance += super.round2(p_data.get("paid"))
                        deb.save()

                        if type == 2:
                            total_payment = 0
                            for inv in p_data.get('invoices'):
                                inv_tax = super.round2(inv['wtax'])
                                inv_tot = super.round2(inv['total'])
                                inv_true = inv_tot - inv_tax

                                # total_payment += (
                                #     super.round2(inv['payment']) +
                                #     (inv_tax * rate)
                                # )

                                invoice = core_models.APOINV.objects.filter(
                                    id=inv['id']
                                ).first()
                                total_tax = 0

                                if invoice.type == 2:
                                    inv2 = core_models.APINV2.objects.filter(
                                        ap=invoice
                                    )
                                    if inv2:
                                        for in2 in inv2:
                                            # tax = (in2.wtax_amt -
                                            #        invoice.applied_tax)
                                            paid = super.round2(in2.paid)
                                            rate = (
                                                super.round2(inv['payment']) /
                                                super.round2(inv['balance'])
                                            )
                                            wamt = in2.wtax_amt
                                            tax_amt = (wamt - paid) * rate
                                            total_tax += super.round2(tax_amt)
                                            total_payment += (
                                                super.round2(tax_amt))

                                            print(f"WTAX INV {in2.wtax_amt}")
                                            print(f"rate INV {rate}")
                                            super.add_JE(
                                                ojdt=ojdt,
                                                account=in2.wtax.account,
                                                debit=0,
                                                credit=super.round2(tax_amt),
                                                remarks="",
                                                post_date=p_data.get(
                                                    "post_date"),
                                                customer=p_data.get("bpid")
                                            )
                                            up_ac = in2.wtax.account
                                            up_ac.balance += (
                                                super.round2(tax_amt))
                                            up_ac.save()

                                            in2.paid = (
                                                super.round2(in2.paid) +
                                                super.round2(tax_amt)
                                            )
                                            in2.save()

                                if inv_true == super.round2(inv['payment']):
                                    invoice.status = 3
                                    invoice.applied_tax = invoice.wtax
                                    print(f"Full Payment {invoice.wtax}")
                                else:
                                    invoice.status = 2
                                    invoice.applied_tax += total_tax
                                    print(f"Partial Payment {total_tax}")
                                apl = super.round2(invoice.applied_amt)
                                pay = super.round2(inv['payment'])
                                invoice.applied_amt = apl + pay
                                invoice.save()

                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=cli,
                                    type="A/P Account"
                                ).account,
                                debit=(
                                    total_payment +
                                    super.round2(p_data.get("paid"))
                                ),
                                credit=0,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=p_data.get("bpid")
                            )
                            cre = super.get_ae(
                                    client=cli,
                                    type="A/P Account"
                                ).account
                            cre.balance -= (
                                total_payment +
                                super.round2(p_data.get("paid"))
                            )
                            cre.save()

                        elif type == 1:
                            super.add_JE(
                                ojdt=ojdt,
                                account=super.get_ae(
                                    client=cli,
                                    type="A/R Account"
                                ).account,
                                debit=super.round2(p_data.get("paid")),
                                credit=0,
                                remarks="",
                                post_date=p_data.get("post_date"),
                                customer=p_data.get("bpid")
                            )
                            cre = super.get_ae(
                                    client=cli,
                                    type="A/R Account"
                                ).account
                            cre.balance -= super.round2(p_data.get("paid"))
                            cre.save()

                        elif type == 3:
                            print(3)
                            for ro in rows:
                                if ro['code'] != "":
                                    super.add_JE(
                                        ojdt=ojdt,
                                        account=super.get_acc(int(ro['code'])),
                                        debit=super.round2(ro['amount']),
                                        credit=0,
                                        remarks="",
                                        post_date=p_data.get("post_date"),
                                        customer=ro['customer']
                                    )
                                    cre = super.get_acc(int(ro['code']))
                                    cre.balance -= super.round2(ro['amount'])
                                    cre.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

            else:
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Successfully Added."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_outgoing_trans(self, request):
        """
        <GET> /api/administration/get_outgoing_trans
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")
        type = request.query_params.get("type")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        fdate = request.query_params.get("date")
        status1 = request.query_params.get("status")
        bp = request.query_params.get("bp")
        bank = request.query_params.get("bank")

        inv = core_models.OUTPAY.objects.filter(
            client=request.user.user_acc.first().client
        )

        if search:
            inv = inv.filter(
                or_num__icontains=search
            )
        if int(bp) != 0:
            if int(type) != 0:
                inv = inv.filter(
                    code__id=int(type)
                )
            else:
                inv = inv.filter(
                    code__type=int(bp)
                )
        if int(bank) != 0:
            inv = inv.filter(
               outBank__account__id=int(bank)
            )
        if dfrom and dto and int(fdate) != 0:
            inv = inv.filter(
                posting_date__range=[dfrom, dto]
            )
        if int(status1) != 0:
            inv = inv.filter(
                status=status1
            )

        inv = inv.order_by('-id')

        result_page = paginator.paginate_queryset(inv, request)
        serializer = u_ser.OutgoingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_outgoing_trans1(self, request):
        """
        <GET> /api/administration/get_outgoing_trans1
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        bank = int(request.query_params.get("bank"))

        inv = core_models.OUTPAY.objects.filter(
            client=request.user.user_acc.first().client,
            reconciled=False,
            outBank__account__id=bank,
            status=6
        ).order_by('-id')

        result_page = paginator.paginate_queryset(inv, request)
        serializer = u_ser.OutgoingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_out_transaction_preview(self, request):
        """
        <GET> /api/administration/id/get_out_transaction_preview
        """
        id = request.query_params.get("id")
        inv = core_models.OUTPAY.objects.filter(
            id=int(id)
        ).first()

        serializer = u_ser.OutSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_je(self, request):
        """
        <GET> /api/administration/add_je
        """
        data = request.data
        p_data = json.loads(data['datas'])
        p_rows = json.loads(data['rows'])
        # inv = p_data.get("invoice")
        # print(data)
        # print(super.round2(data.get("vatAmt")))
        # print(super.round2(data.get("discount")))
        print(p_data)
        print(p_rows)

        with transaction.atomic():
            post = core_models.PostingPeriod.objects.filter(
                from_date__lte=p_data.get("post_date"),
                to_date__gte=p_data.get("post_date")
            ).first()
            jeNo = core_models.DocumentNo.objects.filter(
                client=request.user.user_acc.first().client,
                name='Journal Entry'
            ).first()
            client = request.user.user_acc.first().client
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    return Response({
                        "success": False,
                        "message": "Posting date is closed."
                    }, status=status.HTTP_200_OK)
                else:
                    app = core_models.Approval.objects.get(
                        client=client,
                        module="Journal Entry Approver"
                    )
                    ver = core_models.Approval.objects.get(
                        client=client,
                        module="Journal Entry Verifier"
                    )
                    print("goods")
                    if ver.status == 2 and app.status == 2:
                        ojdt = core_models.OJDT(
                            client=client,
                            no=newJE,
                            origin=1,
                            origin_no=newJE,
                            remarks=p_data.get("remarks"),
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=newJE,
                            total=super.round2(data.get("total")),
                            added=request.user.user_acc.first()
                        )
                        ojdt.save()

                        for rows in p_rows:
                            if rows['code'] != '':
                                acct = super.get_acc(rows['code'])
                                if rows['debit'] == '':
                                    debit = 0
                                    credit = super.round2(rows.get("credit"))
                                    ar = acct
                                    ar.balance -= super.round2(
                                        data.get("total"))
                                    ar.save()
                                else:
                                    credit = 0
                                    debit = super.round2(rows.get("debit"))
                                    ar = acct
                                    ar.balance += super.round2(
                                        data.get("total"))
                                    ar.save()

                                super.add_JE(
                                    ojdt=ojdt,
                                    account=acct,
                                    debit=debit,
                                    credit=credit,
                                    remarks=rows['remarks'],
                                    post_date=p_data.get("post_date"),
                                    customer=rows['customer']
                                )

                        jeNo.no = newJE
                        jeNo.save()

                    else:
                        ojdt = core_models.OJDTTemp(
                            client=client,
                            no=newJE,
                            origin=1,
                            origin_no=newJE,
                            remarks=p_data.get("remarks"),
                            post_date=p_data.get("post_date"),
                            due_date=p_data.get("due_date"),
                            doc_date=p_data.get("doc_date"),
                            trans_no=newJE,
                            total=super.round2(data.get("total")),
                            added=request.user.user_acc.first()
                        )
                        if ver.status == 1:
                            ojdt.status = 4
                            modul = "Journal Entry"
                            end = "is awaiting your verification."
                            mess = f"{modul} {newJE} {end}"
                            super.add_notif(
                                client=client,
                                sender=request.user.user_acc.first(),
                                receiver=ver.user,
                                message=mess,
                                module="/approval?module=1",
                                type=2
                            )
                        elif app.status == 1:
                            ojdt.status = 5
                            modul = "Journal Entry"
                            end = "is awaiting your approval."
                            mess = f"{modul} {newJE} {end}"
                            super.add_notif(
                                client=client,
                                sender=request.user.user_acc.first(),
                                receiver=app.user,
                                message=mess,
                                module="/approval?module=1",
                                type=2
                            )
                        else:
                            ojdt.status = 1
                        ojdt.save()

                        for rows in p_rows:
                            if rows['code'] != '':
                                acct = super.get_acc(rows['code'])
                                if rows['debit'] == '':
                                    debit = 0
                                    credit = super.round2(rows.get("credit"))
                                else:
                                    credit = 0
                                    debit = super.round2(rows.get("debit"))

                                super.add_JETemp(
                                    ojdt=ojdt,
                                    account=acct,
                                    debit=debit,
                                    credit=credit,
                                    remarks=rows['remarks'],
                                    post_date=p_data.get("post_date"),
                                    customer=rows['customer']
                                )

            else:
                print("invalid posting date")
                return Response({
                    "success": False,
                    "message": "Invalid Posting Date."
                }, status=status.HTTP_200_OK)

        return Response({
            "success": True,
            "message": "Journal Entry successfuly added."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_je_trans(self, request):
        """
        <GET> /api/administration/get_je_trans
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        client = request.user.user_acc.first().client

        ftype = request.query_params.get("type")
        # fdate = request.query_params.get("date")
        ffrom = request.query_params.get("from")
        fto = request.query_params.get("to")
        search = request.query_params.get("search")

        today = datetime.now()

        # First day of current month
        fd_month = today.replace(day=1)

        # Last day of last month
        last_day = fd_month - timedelta(days=1)

        # First day of last month
        first_day = last_day.replace(day=1)

        print(f"Lalalalla {11 - abs(fd_month.month - 12)}")
        print(f"Year {fd_month.year}")
        print(f"From: {first_day.strftime('%Y-%m-%d')}")
        print(f"To: {last_day.strftime('%Y-%m-%d')}")

        # inv = core_models.OJDT.objects.filter(
        #     client=request.user.user_acc.first().client
        # ).order_by('-id')

        ojdt = core_models.OJDT.objects.filter(
            client=client
        )
        ojdt_temp = core_models.OJDTTemp.objects.filter(
            client=client,
            status__in=[4, 5]
        )

        if(int(ftype) != 0):
            ojdt = ojdt.filter(origin=int(ftype))
            ojdt_temp = ojdt_temp.filter(origin=int(ftype))

        if(ffrom and fto):
            ojdt = ojdt.filter(post_date__range=[ffrom, fto])
            ojdt_temp = ojdt_temp.filter(post_date__range=[ffrom, fto])

        if search:
            ojdt = ojdt.filter(remarks__icontains=search)
            ojdt_temp = ojdt_temp.filter(remarks__icontains=search)

        ojdt = ojdt.annotate(
            date=F('post_date'),
            amount=F('total'),
            date_added_norm=F('date_added'),
            ref=Value(1, output_field=IntegerField())
        ).values(
            'id', 'no', 'origin', 'date', 'remarks', 'amount',
            'date_added_norm', 'ref'
        )

        ojdt_temp = ojdt_temp.annotate(
            date=F('post_date'),
            amount=F('total'),
            date_added_norm=F('date_added'),
            ref=Value(2, output_field=IntegerField())
        ).values(
            'id', 'no', 'origin', 'date', 'remarks', 'amount',
            'date_added_norm', 'ref'
        )

        combined = ojdt.union(ojdt_temp).order_by('-date_added_norm')

        result_page = paginator.paginate_queryset(combined, request)
        serializer = u_ser.JETransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True)
    def get_je_transaction_preview(self, request, pk):
        """
        <GET> /api/administration/id/get_je_transaction_preview
        """
        inv = core_models.OJDT.objects.filter(
            id=pk
        ).first()

        serializer = u_ser.JETransactionPreviewSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def get_je_transaction_temp_preview(self, request, pk):
        """
        <GET> /api/administration/id/get_je_transaction_temp_preview
        """
        inv = core_models.OJDTTemp.objects.filter(
            id=pk
        ).first()

        serializer = u_ser.JETempTransactionPreviewSerializer(inv, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_bs(self, request):
        """
        <GET> /api/administration/add_bs
        """
        data = request.data
        p_data = json.loads(data['datas'])
        bid = int(data.get("bid"))
        print(data.get("bid"))
        print(p_data)

        with transaction.atomic():
            dup = 0
            added = 0
            bank = core_models.Accounts.objects.filter(
                id=bid
            ).first()
            if bank:
                for row in p_data:
                    v1 = row.get("Date")
                    v2 = row.get("Branch")
                    v3 = row.get("Description")
                    v4 = row.get("Debit")
                    v5 = row.get("Credit")
                    v6 = row.get("Running_Balance")
                    v7 = row.get("Check_No.")

                    uniq = f"{bid} {v1} {v2} {v3} {v4} {v5} {v6} {v7}"
                    exist = core_models.BankRecon.objects.filter(
                        uniq=uniq
                    )
                    if not exist:
                        added += 1
                        addBS = core_models.BankRecon(
                            bank=bank,
                            date=v1,
                            branch=v2,
                            description=v3,
                            debit=super.round2(v4),
                            credit=super.round2(v5),
                            r_balance=super.round2(v6),
                            check_no=v7,
                            uniq=uniq,
                            added_by=request.user.user_acc.first()
                        )
                        addBS.save()
                    else:
                        dup += 1

        return Response({
            "success": True,
            "message": f"{added} Added. {dup} Duplicates."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_bank_statement(self, request):
        """
        <GET> /api/administration/get_bank_statement
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        bid = request.query_params.get("bid")
        stat = request.query_params.get("stat")

        query = core_models.BankRecon.objects.filter(
            bank__id=int(bid),
            status=stat
        ).order_by('-id')

        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.BankStatementSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def up_bank_statement(self, request):
        """
        <GET> /api/administration/up_bank_statement
        """
        data = request.data
        p_data = json.loads(data['datas'])
        today = timezone.now().date()

        with transaction.atomic():
            print(p_data)
            bank_s = core_models.BankRecon.objects.filter(
                id=int(p_data.get("bsid"))
            ).first()
            if bank_s:
                bank_s.status = 2
                bank_s.date_recon = today
                bank_s.invoices = p_data.get("tno")
                bank_s.save()

                if bank_s.debit == 0:
                    up_inv = core_models.OUTPAY.objects.filter(
                        id=int(p_data.get("id"))
                    ).first()
                    if up_inv:
                        up_inv.reconciled = True
                        up_inv.status = 1
                        up_inv.save()
                else:
                    up_inv = core_models.INCPAY.objects.filter(
                        id=int(p_data.get("id"))
                    ).first()
                    if up_inv:
                        up_inv.reconciled = True
                        up_inv.status = 1
                        up_inv.save()

        return Response({
            "success": True,
            "message": "Successfully reconciled."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_inventory(self, request):
        """
        <GET> /api/administration/add_inventory
        """
        data = request.data
        p_data = json.loads(data['datas'])

        with transaction.atomic():
            add_inv = core_models.Inventory(
                client=request.user.user_acc.first().client,
                code=p_data.get("code"),
                name=p_data.get("name"),
                cost=p_data.get("p_cost"),
                sales=p_data.get("p_sales"),
                uom=p_data.get("uom"),
                added_by=request.user.user_acc.first()
            )
            if p_data.get("vendor") != "0":
                bpid = int(p_data.get("vendor"))
                add_inv.vendor = super.get_bp(id=bpid).first()
            if p_data.get("p_cogs") != "0":
                add_inv.cogs = super.get_acc(id=p_data.get("p_cogs"))
            if p_data.get("p_income") != "0":
                add_inv.income = super.get_acc(id=p_data.get("p_income"))
            add_inv.save()

        return Response({
            "success": True,
            "message": f"{p_data['name']} successfully Added."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_inventory(self, request):
        """
        <GET> /api/administration/up_inventory
        """
        data = request.data
        p_data = json.loads(data['datas'])

        with transaction.atomic():
            up_inv = core_models.Inventory.objects.filter(
                id=p_data.get("id")
            ).first()
            if up_inv:
                up_inv.code = p_data.get("code")
                up_inv.name = p_data.get("name")
                up_inv.cost = p_data.get("p_cost")
                up_inv.sales = p_data.get("p_sales")
                up_inv.uom = p_data.get("uom")

                if p_data.get("vendor") != "0":
                    bpid = int(p_data.get("vendor"))
                    up_inv.vendor = super.get_bp(id=bpid).first()
                if p_data.get("p_cogs") != "0":
                    up_inv.cogs = super.get_acc(id=p_data.get("p_cogs"))
                if p_data.get("p_income") != "0":
                    up_inv.income = super.get_acc(id=p_data.get("p_income"))
                up_inv.save()

        return Response({
            "success": True,
            "message": f"{p_data['name']} successfully Updated."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_inventory(self, request):
        """
        <GET> /api/administration/get_inventory
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")

        query = core_models.Inventory.objects.filter(
            client=request.user.user_acc.first().client
        )
        if search:
            query = query.filter(
                name__icontains=search
            )

        query = query.order_by('-id')

        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.InventorySerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_inventory_items(self, request):
        """
        <GET> /api/administration/id/get_inventory_items
        """
        inv = core_models.Inventory.objects.filter(
            client=request.user.user_acc.first().client
        )

        serializer = u_ser.InventorySerializer(inv, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_ar_terms(self, request):
        """
        <GET> /api/administration/add_ar_terms
        """
        data = request.data
        p_data = json.loads(data['datas'])

        with transaction.atomic():
            add_ar = core_models.PaymentTermsAR(
                client=request.user.user_acc.first().client,
                bank_name=p_data.get("bank"),
                acc_name=p_data.get("name"),
                acc_no=p_data.get("no"),
                swift_code=p_data.get("code"),
            )
            add_ar.save()

        return Response({
            "success": True,
            "message": f"{p_data['bank']} successfully Added."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_ar_terms(self, request):
        """
        <GET> /api/administration/up_ar_terms
        """
        data = request.data
        p_data = json.loads(data['datas'])

        with transaction.atomic():
            add_ar = core_models.PaymentTermsAR.objects.filter(
                id=p_data.get("id")
            ).first()
            if add_ar:
                add_ar.bank_name = p_data.get("bank")
                add_ar.acc_name = p_data.get("name")
                add_ar.acc_no = p_data.get("no")
                add_ar.swift_code = p_data.get("code")
                add_ar.save()

        return Response({
            "success": True,
            "message": f"{p_data.get('bank')} successfully Updated."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_terms_payment(self, request):
        """
        <GET> /api/administration/get_ar_terms_payment
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        search = request.query_params.get("search")

        query = core_models.PaymentTermsAR.objects.filter(
            client=request.user.user_acc.first().client
        )
        if search:
            query = query.filter(
                bank_name__icontains=search
            )
        query = query.order_by('-id')

        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.ARTermsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def add_client(self, request, pk=None):
        """
        <GET> /api/administration/add_client
        """
        data = request.data
        p_data = json.loads(data['datas'])
        logo = request.FILES.get('logo')
        name = p_data.get("name")

        cli = core_models.Client(
            client_name=name,
            alias=p_data.get("alias"),
            description=p_data.get("description"),
            c_name=p_data.get("c_name"),
            c_no=p_data.get("c_no"),
            address=p_data.get("address"),
            address1=p_data.get("address1"),
            tin=p_data.get("tin"),
            email=p_data.get("email"),
            license=p_data.get("license"),
        )
        if logo:
            cli.logo = logo

        cli.save()

        return Response({
            "success": True,
            "message": f"{name} successfully added."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_client(self, request, pk=None):
        """
        <GET> /api/administration/up_client
        """
        data = request.data
        p_data = json.loads(data['datas'])
        logo = request.FILES.get('logo')

        cli = core_models.Client.objects.filter(
            id=int(p_data.get("id"))
        ).first()

        name = p_data.get("name")
        if cli:
            cli.client_name = name
            cli.alias = p_data.get("alias")
            cli.description = p_data.get("description")
            cli.c_name = p_data.get("c_name")
            cli.c_no = p_data.get("c_no")
            cli.address = p_data.get("address")
            cli.address1 = p_data.get("address1")
            cli.tin = p_data.get("tin")
            cli.email = p_data.get("email")
            cli.license = p_data.get("license")

            if logo:
                cli.logo = logo

            cli.save()

        return Response({
            "success": True,
            "message": f"{name} successfully updated."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_clients_all(self, request):
        """
        <GET> /api/administration/get_clients_all
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size

        query = core_models.Client.objects.all().order_by('-id')

        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.ClientAllSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_1(self, request):
        """
        <GET> /api/administration/get_approval_1
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")
        app = core_models.Approval.objects.filter(
            client=client,
            module="Journal Entry Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="Journal Entry Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=4)
        if app and user == app.user:
            filters |= Q(status=5)
        if search:
            filters &= Q(no__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.OJDTTemp.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.JETempTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_2(self, request):
        """
        <GET> /api/administration/get_approval_2
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/R Invoice Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="A/R Invoice Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=5)
        if app and user == app.user:
            filters |= Q(status=6)
        if search:
            filters &= Q(invoice_num__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.AROINV.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.ARSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_3(self, request):
        """
        <GET> /api/administration/get_approval_3
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/R Credit Memo Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="A/R Credit Memo Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=5)
        if app and user == app.user:
            filters |= Q(status=6)
        if search:
            filters &= Q(invoice_num__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.AROCRM.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.ARCMSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_4(self, request):
        """
        <GET> /api/administration/get_approval_4
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/P Invoice Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="A/P Invoice Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=5)
        if app and user == app.user:
            filters |= Q(status=6)
        if search:
            filters &= Q(invoice_num__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.APOINV.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.APSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_5(self, request):
        """
        <GET> /api/administration/get_approval_5
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/P Credit Memo Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="A/P Credit Memo Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=5)
        if app and user == app.user:
            filters |= Q(status=6)
        if search:
            filters &= Q(invoice_num__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.APOCRM.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.APCMSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_6(self, request):
        """
        <GET> /api/administration/get_approval_6
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="Incoming Payment Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="Incoming Payment Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=3)
        if app and user == app.user:
            filters |= Q(status=4)
        if search:
            filters &= Q(doc_no__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.INCPAY.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.IncomingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def get_approval_7(self, request):
        """
        <GET> /api/administration/get_approval_7
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        user = request.user.user_acc.first()
        client = request.user.user_acc.first().client
        search = request.query_params.get("search")

        app = core_models.Approval.objects.filter(
            client=client,
            module="Outgoing Payment Approver"
        ).first()
        ver = core_models.Approval.objects.filter(
            client=client,
            module="Outgoing Payment Verifier"
        ).first()

        filters = Q()
        if ver and user == ver.user:
            filters |= Q(status=3)
        if app and user == app.user:
            filters |= Q(status=4)
        if search:
            filters &= Q(doc_no__icontains=search)
        if not filters:
            return Response({"count": 0}, status=200)

        query = core_models.OUTPAY.objects.filter(filters)
        query = query.order_by('-id')
        result_page = paginator.paginate_queryset(query, request)
        serializer = u_ser.OutgoingTransactionsSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def up_app2(self, request):
        """
        <GET> /api/administration/up_app2
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/R Invoice Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="A/R Invoice Verifier"
        # )

        with transaction.atomic():
            ar = core_models.AROINV.objects.filter(id=id).first()
            if ar.cancelation:
                mess = f"A/R Invoice {ar.invoice_num} has been verified."
                mess6 = f"A/R Invoice {ar.invoice_num} has been approved."
            else:
                mess = f"A/R Invoice {ar.invoice_num} has been verified."
                mess6 = f"A/R Invoice {ar.invoice_num} has been approved."

            if status1 == 3:
                ar.status = 7
                ar.date_dec = today
                ar.declined = request.user.user_acc.first()
                ar.save()
                mess = f"A/R Invoice {ar.invoice_num} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=ar.added,
                    message=mess,
                    module="/sales/invoice",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    ar.status = 6
                    ar.date_ver = today
                    ar.verified = request.user.user_acc.first()
                    ar.save()
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=ar.added,
                        message=mess,
                        module="/sales/invoice",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"A/R Invoice {ar.invoice_num} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=2",
                        type=2
                    )
                else:
                    print("Posted dapat")

                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=ar.added,
                        message=mess6,
                        module="/sales/invoice",
                        type=2
                    )
                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1
                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=2,
                        origin_no=ar.invoice_num,
                        remarks=f"Based on A/R Invoice {ar.invoice_num}",
                        post_date=ar.posting_date,
                        due_date=ar.due_date,
                        doc_date=ar.doc_date,
                        trans_no=ar.id,
                        total=ar.total
                    )
                    ojdt.save()

                    ar_amt = ar.total
                    super.add_JE(
                        ojdt=ojdt,
                        account=super.get_ae(
                            client=client,
                            type="A/R Account"
                        ).account,
                        debit=ar_amt if not ar.cancelation else 0,
                        credit=0 if not ar.cancelation else ar_amt,
                        remarks="",
                        post_date=ar.posting_date,
                        customer=ar.code.id
                    )
                    ar_acc = super.get_ae(
                            client=client,
                            type="A/R Account"
                        ).account
                    if ar.cancelation:
                        ar_acc.balance -= ar_amt
                    else:
                        ar_acc.balance += ar_amt
                    ar_acc.save()

                    if ar.vat > 0:
                        vat_amt = ar.vat
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="Output VAT"
                            ).account,
                            debit=0 if not ar.cancelation else vat_amt,
                            credit=vat_amt if not ar.cancelation else 0,
                            remarks="",
                            post_date=ar.posting_date,
                            customer=ar.code.id
                        )
                        vat = super.get_ae(
                                client=client,
                                type="Output VAT"
                            ).account
                        if ar.cancelation:
                            vat.balance -= vat_amt
                        else:
                            vat.balance += vat_amt
                        vat.save()

                    for rows in ar.invRows.all():
                        if int(rows.vatable) == 1:
                            si = (super.round2(rows.amount) / Decimal("1.12") -
                                  super.round2(rows.discount))
                        else:
                            si = (super.round2(rows.amount) -
                                  super.round2(rows.discount))
                        super.add_JE(
                            ojdt=ojdt,
                            account=rows.account,
                            debit=0 if not ar.cancelation else si,
                            credit=si if not ar.cancelation else 0,
                            remarks=rows.description,
                            post_date=ar.posting_date,
                            customer=rows.customer.id
                        )
                        acc = super.get_acc(int(rows.account.id))
                        if ar.cancelation:
                            acc.balance -= si
                        else:
                            acc.balance += si
                        acc.save()

                    if ar.cancelation:
                        ar.status = 3
                        ar.canceledAR.status = 4
                        ar.canceledAR.save()
                    else:
                        ar.status = 1
                    ar.date_app = today
                    ar.approved = request.user.user_acc.first()
                    ar.save()

                    jeNo.no = newJE
                    jeNo.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app3(self, request):
        """
        <GET> /api/administration/up_app3
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/R Credit Memo Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="A/R Credit Memo Verifier"
        # )
        with transaction.atomic():
            cm = core_models.AROCRM.objects.filter(id=id).first()
            if status1 == 3:
                cm.status = 7
                cm.date_dec = today
                cm.declined = request.user.user_acc.first()
                cm.save()
                mess = f"A/R CM Invoice {cm.invoice_num} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=cm.added,
                    message=mess,
                    module="/sales/credit-memo",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    cm.status = 6
                    cm.date_ver = today
                    cm.verified = request.user.user_acc.first()
                    cm.save()
                    modul = "A/P CM Invoice"
                    mess = f"{modul} {cm.invoice_num} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=cm.added,
                        message=mess,
                        module="/sales/credit-memo",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"A/P CM Invoice {cm.invoice_num} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=3",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    modul = "A/P CM Invoice"
                    mess = f"{modul} {cm.invoice_num} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=cm.added,
                        message=mess,
                        module="/sales/credit-memo",
                        type=2
                    )

                    if (cm.ar.total - (
                        cm.ar.applied_amt + cm.ar.applied_tax
                            )) == cm.total:
                        cm.ar.status = 3
                        cm.ar.save()

                    cm.ar.applied_amt = (
                        super.round2(cm.ar.applied_amt) +
                        super.round2(cm.total) -
                        super.round2(cm.wtax))
                    cm.ar.applied_tax = (
                        super.round2(cm.ar.applied_tax) +
                        super.round2(cm.wtax))
                    cm.ar.save()

                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1

                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=3,
                        origin_no=cm.invoice_num,
                        remarks=f"Based on A/R Credit Memo {cm.invoice_num}",
                        post_date=cm.posting_date,
                        due_date=cm.due_date,
                        doc_date=cm.doc_date,
                        trans_no=cm.id,
                        total=cm.total
                    )
                    ojdt.save()

                    ar_amt = cm.total
                    super.add_JE(
                        ojdt=ojdt,
                        account=super.get_ae(
                            client=client,
                            type="A/R Account"
                        ).account,
                        debit=abs(ar_amt) if ar_amt < 0 else 0,
                        credit=abs(ar_amt) if ar_amt > 0 else 0,
                        remarks="",
                        post_date=cm.posting_date,
                        customer=cm.code.id
                    )
                    ar_acc = super.get_ae(
                            client=client,
                            type="A/R Account"
                        ).account
                    if (cm.total > 0):
                        ar_acc.balance -= cm.total
                    else:
                        ar_acc.balance += cm.total
                    ar_acc.save()

                    if cm.vat > 0:
                        vat_amt = cm.vat
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="Output VAT"
                            ).account,
                            debit=abs(vat_amt) if vat_amt > 0 else 0,
                            credit=abs(vat_amt) if vat_amt < 0 else 0,
                            remarks="",
                            post_date=cm.posting_date,
                            customer=cm.code.id
                        )
                        vat = super.get_ae(
                                client=client,
                                type="Output VAT"
                            ).account
                        if vat_amt > 0:
                            vat.balance -= vat_amt
                        else:
                            vat.balance += vat_amt
                        vat.save()

                    for rows in cm.crmRows.all():
                        if int(rows.vatable) == 1:
                            si = (super.round2(rows.amount) / Decimal("1.12") -
                                  super.round2(rows.discount))
                        else:
                            si = (super.round2(rows.amount) -
                                  super.round2(rows.discount))
                        super.add_JE(
                            ojdt=ojdt,
                            account=rows.account,
                            debit=abs(si) if si > 0 else 0,
                            credit=abs(si) if si < 0 else 0,
                            remarks=rows.description,
                            post_date=cm.posting_date,
                            customer=rows.customer.id
                        )
                        acc = super.get_acc(int(rows.account.id))
                        if si < 0:
                            acc.balance += si
                        else:
                            acc.balance -= si
                        acc.save()

                    cm.status = 3
                    cm.date_app = today
                    cm.approved = request.user.user_acc.first()
                    cm.save()

                    jeNo.no = newJE
                    jeNo.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app4(self, request):
        """
        <GET> /api/administration/up_app4
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/P Invoice Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="A/P Invoice Verifier"
        # )

        with transaction.atomic():
            ap = core_models.APOINV.objects.filter(id=id).first()
            if ap.cancelation:
                mess = f"A/R Invoice {ap.invoice_num} has been verified."
                mess6 = f"A/R Invoice {ap.invoice_num} has been approved."
            else:
                mess = f"A/R Invoice {ap.invoice_num} has been verified."
                mess6 = f"A/R Invoice {ap.invoice_num} has been approved."

            if status1 == 3:
                ap.status = 7
                ap.date_dec = today
                ap.declined = request.user.user_acc.first()
                ap.save()
                mess = f"A/P Invoice {ap.invoice_num} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=ap.added,
                    message=mess,
                    module="/purchasing/invoice",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    ap.status = 6
                    ap.date_ver = today
                    ap.verified = request.user.user_acc.first()
                    ap.save()
                    mess = f"A/P Invoice {ap.invoice_num} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=ap.added,
                        message=mess,
                        module="/purchasing/invoice",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"A/P Invoice {ap.invoice_num} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=4",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    mess = f"A/P Invoice {ap.invoice_num} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=ap.added,
                        message=mess6,
                        module="/purchasing/invoice",
                        type=2
                    )
                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1
                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=4,
                        origin_no=ap.invoice_num,
                        remarks=f"Based on A/P Invoice {ap.invoice_num}",
                        post_date=ap.posting_date,
                        due_date=ap.due_date,
                        doc_date=ap.doc_date,
                        trans_no=ap.id,
                        total=ap.total
                    )
                    ojdt.save()

                    # ap_amt = ap.total - ap.wtax
                    if ap.type == 1:
                        ap_amt = (
                            super.round2(ap.total) -
                            super.round2(ap.wtax)
                        )
                    else:
                        ap_amt = super.round2(ap.total)
                    super.add_JE(
                        ojdt=ojdt,
                        account=super.get_ae(
                            client=client,
                            type="A/P Account"
                        ).account,
                        debit=0 if not ap.cancelation else ap_amt,
                        credit=ap_amt if not ap.cancelation else 0,
                        remarks="",
                        post_date=ap.posting_date,
                        customer=ap.code.id
                    )
                    ar_acc = super.get_ae(
                            client=client,
                            type="A/P Account"
                        ).account
                    ar_acc.balance += ap_amt
                    ar_acc.save()

                    for rows in ap.invAPRows.all():
                        # if int(rows.vatable) == 1:
                        #     si = (super.round2(rows.amount)
                        # / Decimal("1.12") -
                        #           super.round2(rows.discount))
                        # else:
                        #     si = (super.round2(rows.amount) -
                        #           super.round2(rows.discount))
                        ramt = super.round2(rows.amount)
                        rdis = super.round2(rows.discount)
                        vat = Decimal("1.12")
                        if int(rows.vatable) == 1:
                            si = (super.round2(ramt / vat) - rdis)
                        else:
                            si = (ramt - rdis)
                        if ap.type == 2:
                            super.add_JE(
                                ojdt=ojdt,
                                account=rows.account,
                                debit=si if not ap.cancelation else 0,
                                credit=0 if not ap.cancelation else si,
                                remarks=rows.description,
                                post_date=ap.posting_date,
                                customer=rows.customer.id
                            )
                            acc = super.get_acc(int(rows.account.id))
                            acc.balance += si
                            acc.save()
                        else:
                            ia = super.get_ae(
                                client=client,
                                type="Inventory Account"
                            )
                            if not ia.account:
                                m1 = "Please select"
                                mes = f"{m1} Inventory Account."
                                raise PermissionDenied(mes)
                            super.add_JE(
                                ojdt=ojdt,
                                account=ia.account,
                                debit=si if not ap.cancelation else 0,
                                credit=0 if not ap.cancelation else si,
                                remarks=rows.description,
                                post_date=ap.posting_date,
                                customer=rows.customer.id
                            )
                            acc = ia.account
                            acc.balance += si
                            acc.save()
                            upQty = core_models.Inventory.objects.get(
                                id=rows.product.id
                            )
                            upQty.stock += super.round2(rows.qty)
                            upQty.save()
                            # asdfsa
                        # super.add_JE(
                        #     ojdt=ojdt,
                        #     account=rows.account,
                        #     debit=ap,
                        #     credit=0,
                        #     remarks=rows.description,
                        #     post_date=ap.posting_date,
                        #     customer=rows.customer.id
                        # )
                        # acc = super.get_acc(int(rows.account.id))
                        # acc.balance += ap
                        # acc.save()

                    if ap.vat > 0:
                        vat_amt = ap.vat
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="Input VAT"
                            ).account,
                            debit=vat_amt if not ap.cancelation else 0,
                            credit=0 if not ap.cancelation else vat_amt,
                            remarks="",
                            post_date=ap.posting_date,
                            customer=ap.code.id
                        )
                        vat = super.get_ae(
                                client=client,
                                type="Input VAT"
                            ).account
                        vat.balance += vat_amt
                        vat.save()

                    if ap.type == 1:
                        for rows in ap.invAPTax.all():
                            super.add_JE(
                                ojdt=ojdt,
                                account=rows.wtax.account,
                                debit=0
                                if not ap.cancelation else rows.wtax_amt,
                                credit=rows.wtax_amt
                                if not ap.cancelation else 0,
                                remarks=super.get_ae(
                                    id=rows.wtax.id).type,
                                post_date=ap.posting_date,
                                customer=ap.code.id
                            )
                            acc1 = rows.wtax.account
                            acc1.balance += Decimal(rows.wtax_amt)
                            acc1.save()

                    if ap.cancelation:
                        ap.status = 3
                        ap.canceledAP.status = 4
                        ap.canceledAP.save()
                    else:
                        ap.status = 1
                    ap.date_app = today
                    ap.approved = request.user.user_acc.first()
                    ap.save()

                    jeNo.no = newJE
                    jeNo.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app5(self, request):
        """
        <GET> /api/administration/up_app5
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="A/P Credit Memo Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="A/P Credit Memo Verifier"
        # )

        with transaction.atomic():
            cm = core_models.APOCRM.objects.filter(id=id).first()
            if status1 == 3:
                cm.status = 7
                cm.date_dec = today
                cm.declined = request.user.user_acc.first()
                cm.save()
                mess = f"A/P CM Invoice {cm.invoice_num} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=cm.added,
                    message=mess,
                    module="/purchasing/credit-memo",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    cm.status = 6
                    cm.date_ver = today
                    cm.verified = request.user.user_acc.first()
                    cm.save()
                    modul = "A/P CM Invoice"
                    mess = f"{modul} {cm.invoice_num} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=cm.added,
                        message=mess,
                        module="/purchasing/credit-memo",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"A/P CM Invoice {cm.invoice_num} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=5",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    modul = "A/P CM Invoice"
                    mess = f"{modul} {cm.invoice_num} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=cm.added,
                        message=mess,
                        module="/purchasing/credit-memo",
                        type=2
                    )
                    if (cm.ap.total - (
                        cm.ap.applied_amt + cm.ap.applied_tax
                            )) == cm.total:
                        cm.ap.status = 3
                        cm.ap.save()

                    cm.ap.applied_amt = (
                        super.round2(cm.ap.applied_amt) +
                        super.round2(cm.total) -
                        super.round2(cm.wtax))
                    cm.ap.applied_tax = (
                        super.round2(cm.ap.applied_tax) +
                        super.round2(cm.wtax))
                    cm.ap.save()

                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1

                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=5,
                        origin_no=cm.invoice_num,
                        remarks=f"Based on A/P Credit Memo {cm.invoice_num}",
                        post_date=cm.posting_date,
                        due_date=cm.due_date,
                        doc_date=cm.doc_date,
                        trans_no=cm.id,
                        total=cm.total
                    )
                    ojdt.save()

                    # ar_amt = cm.total
                    # if cm.type == 1:
                    # ar_amt = (
                    #     super.round2(cm.total) -
                    #     super.round2(cm.wtax)
                    # )
                    # else:
                    #     ar_amt = super.round2(cm.total)
                    ar_amt = super.round2(cm.total)
                    super.add_JE(
                        ojdt=ojdt,
                        account=super.get_ae(
                            client=client,
                            type="A/P Account"
                        ).account,
                        debit=abs(ar_amt) if ar_amt > 0 else 0,
                        credit=abs(ar_amt) if ar_amt < 0 else 0,
                        remarks="",
                        post_date=cm.posting_date,
                        customer=cm.code.id
                    )
                    ar_acc = super.get_ae(
                            client=client,
                            type="A/P Account"
                        ).account
                    if (cm.total > 0):
                        ar_acc.balance -= cm.total
                    else:
                        ar_acc.balance += cm.total
                    ar_acc.save()

                    for rows in cm.crmAPRows.all():
                        # if int(rows.vatable) == 1:
                        #     si = (super.round2(rows.amount)
                        # / Decimal("1.12") -
                        #           super.round2(rows.discount))
                        # else:
                        #     si = (super.round2(rows.amount) -
                        #           super.round2(rows.discount))
                        ramt = super.round2(rows.amount)
                        rdis = super.round2(rows.discount)
                        vat = Decimal("1.12")
                        if int(rows.vatable) == 1:
                            si = (super.round2(ramt / vat) - rdis)
                        else:
                            si = (ramt - rdis)
                        super.add_JE(
                            ojdt=ojdt,
                            account=rows.account,
                            debit=abs(si) if si < 0 else 0,
                            credit=abs(si) if si > 0 else 0,
                            remarks=rows.description,
                            post_date=cm.posting_date,
                            customer=rows.customer.id
                        )
                        acc = super.get_acc(int(rows.account.id))
                        if si < 0:
                            acc.balance += si
                        else:
                            acc.balance -= si
                        acc.save()

                    if cm.vat > 0:
                        vat_amt = cm.vat
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="Input VAT"
                            ).account,
                            debit=abs(vat_amt) if vat_amt < 0 else 0,
                            credit=abs(vat_amt) if vat_amt > 0 else 0,
                            remarks="",
                            post_date=cm.posting_date,
                            customer=cm.code.id
                        )
                        vat = super.get_ae(
                                client=client,
                                type="Input VAT"
                            ).account
                        if vat_amt > 0:
                            vat.balance -= vat_amt
                        else:
                            vat.balance += vat_amt
                        vat.save()

                    for index, rows in enumerate(cm.crmAPTax.all()):
                        # super.add_JE(
                        #     ojdt=ojdt,
                        #     account=rows.wtax.account,
                        #     debit=abs(rows.wtax_amt)
                        #     if rows.wtax_amt > 0 else 0,
                        #     credit=abs(rows.wtax_amt)
                        #     if rows.wtax_amt < 0 else 0,
                        #     remarks=super.get_ae(
                        #         id=rows.wtax.id).type,
                        #     post_date=cm.posting_date,
                        #     customer=cm.code.id
                        # )
                        # acc1 = rows.wtax.account
                        # if rows.wtax_amt > 0:
                        #     acc1.balance -= rows.wtax_amt
                        # else:
                        #     acc1.balance += rows.wtax_amt
                        # acc1.save()

                        tax_row = cm.ap.invAPTax.all()[index]
                        if tax_row.paid:
                            tax_row.paid += rows.wtax_amt
                        else:
                            tax_row.paid = rows.wtax_amt
                        tax_row.save()

                    cm.status = 3
                    cm.date_app = today
                    cm.approved = request.user.user_acc.first()
                    cm.save()

                    jeNo.no = newJE
                    jeNo.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app6(self, request):
        """
        <GET> /api/administration/up_app6
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="Incoming Payment Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="Incoming Payment Verifier"
        # )

        with transaction.atomic():
            inv = core_models.INCPAY.objects.filter(id=id).first()
            if status1 == 3:
                inv.status = 5
                inv.date_dec = today
                inv.declined = request.user.user_acc.first()
                inv.save()
                mess = f"Incoming Payment {inv.doc_no} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=inv.added,
                    message=mess,
                    module="/banking/incoming-payment",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    inv.status = 4
                    inv.date_ver = today
                    inv.verified = request.user.user_acc.first()
                    inv.save()
                    mess = f"Incoming Payment {inv.doc_no} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/banking/incoming-payment",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"Incoming Payment {inv.doc_no} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=6",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    mess = f"Incoming Payment {inv.doc_no} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/banking/incoming-payment",
                        type=2
                    )
                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1
                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=6,
                        origin_no=inv.doc_no,
                        remarks=f"Based on Incoming Payment {inv.doc_no}",
                        post_date=inv.posting_date,
                        due_date=inv.due_date,
                        doc_date=inv.doc_date,
                        trans_no=inv.id,
                        total=inv.total_amt
                    )
                    ojdt.save()

                    super.add_JE(
                        ojdt=ojdt,
                        account=inv.incBank.first().account,
                        debit=inv.total_amt,
                        credit=0,
                        remarks="",
                        post_date=inv.posting_date,
                        customer=inv.code.id
                    )
                    deb = inv.incBank.first().account
                    deb.balance += inv.total_amt
                    deb.save()

                    if inv.type == 1:
                        total_payment = 0
                        for inv5 in inv.incInv.all():
                            print(f"Invoice ID: {inv5.id}")
                            # inv_tax = super.round2(inv5.wtax)
                            inv_tot = super.round2(inv5.amount)
                            # inv_true = inv_tot - inv_tax
                            # rate = super.round2(inv.total_amt) / inv_tot

                            # print(f"inv_tax {inv5.wtax}")
                            # print(f"inv_tot {inv_tot}")
                            # print(f"inv5.amount {inv5.amount}")
                            # print(f"inv_true {inv_true}")
                            # print(f"rate {rate}")

                            # total_payment += (inv_tax * rate)
                            # invoice = core_models.AROINV.objects.filter(
                            #     id=inv.invoice.id
                            # ).first()

                            # inv2 = core_models.ARINV2.objects.filter(
                            #     ar=invoice
                            # )
                            # if inv2:
                            total_tax = 0
                            for in2 in inv5.invoice.invTax.all():
                                print(f"AR Invoice ID: {in2.id}")
                                print(f"wtax_amt {in2.wtax_amt}")
                                # tax = (
                                #     in2.wtax_amt - inv5.invoice.applied_tax)
                                # print(f"tax {tax}")
                                # print(f"tax * rate {tax * rate}")

                                print(f"Amount Paid: {inv5.pay_bal}")
                                print(f"Invoice Amount: {inv5.amount}")
                                rate = inv5.pay_bal / inv5.amount
                                print(f"Final Rate: {rate}")
                                paid = super.round2(in2.paid)
                                tax_amt = (in2.wtax_amt - paid) * rate
                                print(f"Final Tax: {super.round2(tax_amt)}")
                                total_tax += super.round2(tax_amt)
                                total_payment += super.round2(tax_amt)
                                super.add_JE(
                                    ojdt=ojdt,
                                    account=in2.wtax.account,
                                    debit=super.round2(tax_amt),
                                    credit=0,
                                    remarks="",
                                    post_date=inv.posting_date,
                                    customer=inv.code.id
                                )
                                up_ac = in2.wtax.account
                                up_ac.balance += super.round2(tax_amt)
                                up_ac.save()

                                in2.paid = (
                                    super.round2(in2.paid) +
                                    super.round2(tax_amt)
                                )
                                in2.save()

                            if inv_tot == super.round2(inv5.pay_bal):
                                inv5.invoice.status = 3
                                inv5.invoice.applied_tax = inv5.invoice.wtax
                                print(f"Full Payment {inv5.invoice.wtax}")
                            else:
                                inv5.invoice.status = 2
                                inv5.invoice.applied_tax += total_tax
                                print(f"Partial Payment {total_tax}")

                            apl = super.round2(inv5.invoice.applied_amt)
                            pay = super.round2(inv5.pay_bal)
                            inv5.invoice.applied_amt = apl + pay
                            inv5.invoice.save()

                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account,
                            debit=0,
                            credit=total_payment + super.round2(inv.total_amt),
                            remarks="",
                            post_date=inv.posting_date,
                            customer=inv.code.id
                        )
                        cre = super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account
                        cre.balance -= (
                            total_payment + super.round2(inv.total_amt)
                        )
                        cre.save()

                    elif inv.type == 2:
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=0,
                            credit=super.round2(inv.total_amt),
                            remarks="",
                            post_date=inv.posting_date,
                            customer=inv.code.id
                        )
                        cre = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        cre.balance -= super.round2(inv.total_amt)
                        cre.save()

                    elif inv.type == 3:
                        print(3)
                        # for ro in rows:
                        #     if ro['code'] != "":
                        #         super.add_JE(
                        #             ojdt=ojdt,
                        #             account=super.get_acc(int(ro['code'])),
                        #             debit=0,
                        #             credit=super.round2(ro['amount']),
                        #             remarks="",
                        #             post_date=p_data.get("post_date"),
                        #             customer=ro['customer']
                        #         )
                        #         cre = super.get_acc(int(ro['code']))
                        #         cre.balance -= super.round2(ro['amount'])
                        #         cre.save()

                    jeNo.no = newJE
                    jeNo.save()

                    inv.status = 6
                    inv.date_app = today
                    inv.approved = request.user.user_acc.first()
                    inv.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app7(self, request):
        """
        <GET> /api/administration/up_app7
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="Outgoing Payment Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="Outgoing Payment Verifier"
        # )

        with transaction.atomic():
            inv = core_models.OUTPAY.objects.filter(id=id).first()
            if status1 == 3:
                inv.status = 5
                inv.date_dec = today
                inv.declined = request.user.user_acc.first()
                inv.save()
                mess = f"Outgoing Payment {inv.doc_no} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=inv.added,
                    message=mess,
                    module="/banking/outgoing-payment",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    inv.status = 4
                    inv.date_ver = today
                    inv.verified = request.user.user_acc.first()
                    inv.save()
                    mess = f"Outgoing Payment {inv.doc_no} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/banking/outgoing-payment",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"Outgoing Payment {inv.doc_no} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=7",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    mess = f"Outgoing Payment {inv.doc_no} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/banking/outgoing-payment",
                        type=2
                    )
                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1
                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=7,
                        origin_no=inv.doc_no,
                        remarks=f"Based on Outgoing Payment {inv.doc_no}",
                        post_date=inv.posting_date,
                        due_date=inv.due_date,
                        doc_date=inv.doc_date,
                        trans_no=inv.id,
                        total=inv.total_amt
                    )
                    ojdt.save()

                    super.add_JE(
                        ojdt=ojdt,
                        account=inv.outBank.first().account,
                        debit=0,
                        credit=inv.total_amt,
                        remarks="",
                        post_date=inv.posting_date,
                        customer=inv.code.id
                    )
                    deb = inv.outBank.first().account
                    deb.balance += inv.total_amt
                    deb.save()

                    if inv.type == 2:
                        total_payment = 0
                        for inv5 in inv.outInv.all():
                            # inv_tax = super.round2(inv5.wtax)
                            inv_tot = super.round2(inv5.amount)
                            # inv_true = inv_tot - inv_tax
                            # rate = super.round2(inv.total_amt) / inv_tot

                            # total_payment += (
                            #     super.round2(inv.total_amt) +
                            #     inv5.pay_tax
                            # )
                            print(f"Invoice here: {inv5.id}")
                            invoice = core_models.APOINV.objects.filter(
                                id=inv5.invoice.id
                            ).first()
                            total_tax = 0

                            if invoice.type == 2:
                                inv2 = core_models.APINV2.objects.filter(
                                    ap=invoice
                                )
                                if inv2:
                                    for in2 in inv2:
                                        # tax = (in2.wtax_amt -
                                        #         invoice.applied_tax)
                                        paid = super.round2(in2.paid)
                                        rate = inv5.pay_bal / inv5.amount
                                        tax_amt = (in2.wtax_amt - paid) * rate
                                        total_tax += super.round2(tax_amt)
                                        total_payment += super.round2(tax_amt)
                                        print(f"WTAX INV {in2.wtax_amt}")
                                        print(f"rate INV {rate}")

                                        super.add_JE(
                                            ojdt=ojdt,
                                            account=in2.wtax.account,
                                            debit=0,
                                            credit=super.round2(tax_amt),
                                            remarks="",
                                            post_date=inv.posting_date,
                                            customer=inv.code.id
                                        )
                                        up_ac = in2.wtax.account
                                        up_ac.balance += super.round2(tax_amt)
                                        up_ac.save()

                                        in2.paid = (
                                            super.round2(in2.paid) +
                                            super.round2(tax_amt)
                                        )
                                        in2.save()

                            if inv_tot == super.round2(inv5.pay_bal):
                                invTax = inv5.invoice.wtax
                                inv5.invoice.status = 3
                                inv5.invoice.applied_tax = invTax
                                print(f"Full Payment {inv5.invoice.wtax}")
                            else:
                                inv5.invoice.status = 2
                                inv5.invoice.applied_tax += total_tax
                                print(f"Partial Payment {total_tax}")
                            apl = super.round2(inv5.invoice.applied_amt)
                            pay = super.round2(inv5.pay_bal)
                            inv5.invoice.applied_amt = apl + pay
                            inv5.invoice.save()

                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=total_payment + super.round2(inv.total_amt),
                            credit=0,
                            remarks="",
                            post_date=inv.posting_date,
                            customer=inv.code.id
                        )
                        cre = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        cre.balance -= (
                            total_payment +
                            super.round2(inv.total_amt)
                        )
                        cre.save()

                    elif inv.type == 1:
                        super.add_JE(
                            ojdt=ojdt,
                            account=super.get_ae(
                                client=client,
                                type="A/R Account"
                            ).account,
                            debit=super.round2(inv.total_amt),
                            credit=0,
                            remarks="",
                            post_date=inv.posting_date,
                            customer=inv.code.id
                        )
                        cre = super.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        cre.balance -= super.round2(inv.total_amt)
                        cre.save()

                    elif inv.type == 3:
                        print(3)
                        # for ro in rows:
                        #     if ro['code'] != "":
                        #         super.add_JE(
                        #             ojdt=ojdt,
                        #             account=super.get_acc(int(ro['code'])),
                        #             debit=0,
                        #             credit=super.round2(ro['amount']),
                        #             remarks="",
                        #             post_date=p_data.get("post_date"),
                        #             customer=ro['customer']
                        #         )
                        #         cre = super.get_acc(int(ro['code']))
                        #         cre.balance -= super.round2(ro['amount'])
                        #         cre.save()

                    jeNo.no = newJE
                    jeNo.save()

                    inv.status = 6
                    inv.date_app = today
                    inv.approved = request.user.user_acc.first()
                    inv.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def up_app1(self, request):
        """
        <GET> /api/administration/up_app1
        """
        data = request.data
        print(data)
        id = int(data.get("id"))
        status1 = int(data.get("status"))
        client = request.user.user_acc.first().client
        today = timezone.now()

        app = core_models.Approval.objects.filter(
            client=client,
            module="Journal Entry Approver"
        ).first()
        # ver = core_models.Approval.objects.get(
        #     client=client,
        #     module="Journal Entry Verifier"
        # )

        with transaction.atomic():
            inv = core_models.OJDTTemp.objects.filter(id=id).first()
            if status1 == 3:
                inv.status = 6
                inv.date_dec = today
                inv.declined = request.user.user_acc.first()
                inv.save()
                mess = f"Journal Entry {inv.no} has been declined."
                super.add_notif(
                    client=client,
                    sender=request.user.user_acc.first(),
                    receiver=inv.added,
                    message=mess,
                    module="/financials/journal-entry",
                    type=2
                )
            else:
                if status1 == 1 and app.status == 1 and app.user:
                    inv.status = 5
                    inv.date_ver = today
                    inv.verified = request.user.user_acc.first()
                    inv.save()
                    mess = f"Journal Entry {inv.no} has been verified."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/financials/journal-entry",
                        type=2
                    )
                    end = "is awaiting your approval."
                    mess1 = f"Journal Entry {inv.no} {end}"
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=app.user,
                        message=mess1,
                        module="/approval?module=1",
                        type=2
                    )
                else:
                    print("Posted dapat")
                    mess = f"Journal Entry {inv.no} has been approved."
                    super.add_notif(
                        client=client,
                        sender=request.user.user_acc.first(),
                        receiver=inv.added,
                        message=mess,
                        module="/financials/journal-entry",
                        type=2
                    )
                    jeNo = core_models.DocumentNo.objects.filter(
                        client=request.user.user_acc.first().client,
                        name='Journal Entry'
                    ).first()
                    newJE = int(jeNo.no) + 1
                    ojdt = core_models.OJDT(
                        client=client,
                        no=newJE,
                        origin=1,
                        origin_no=newJE,
                        remarks=inv.remarks,
                        post_date=inv.post_date,
                        due_date=inv.due_date,
                        doc_date=inv.doc_date,
                        trans_no=newJE,
                        total=inv.total,
                        added=request.user.user_acc.first()
                    )
                    ojdt.save()

                    for rows in inv.ojdtTemp1.all():
                        super.add_JE(
                            ojdt=ojdt,
                            account=rows.account,
                            debit=rows.debit,
                            credit=rows.credit,
                            remarks=rows.remarks,
                            post_date=rows.post_date,
                            customer=rows.bp.id if rows.bp else ""
                        )

                        jeNo.no = newJE
                        jeNo.save()

                    inv.status = 2
                    inv.date_app = today
                    inv.approved = request.user.user_acc.first()
                    inv.save()

        if status1 == 3:
            statusM = "declined"
        elif status1 == 1:
            statusM = "verified"
        else:
            statusM = "approved"

        return Response({
            "success": True,
            "message": f"Successfully {statusM}."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_customers(self, request):
        """
        <GET> /api/administration/get_customers
        """
        client = request.user.user_acc.first().client

        cs = core_models.BusinessPartner.objects.filter(
            client=client,
            type=1,
            status=1,
        )

        arr = []
        if cs:
            for c in cs:
                arr.append({
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                })

        return Response({
            "success": True,
            "data": arr,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_vendors(self, request):
        """
        <GET> /api/administration/get_vendors
        """
        client = request.user.user_acc.first().client

        cs = core_models.BusinessPartner.objects.filter(
            client=client,
            type=2,
            status=1,
        )

        arr = []
        if cs:
            for c in cs:
                arr.append({
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                })

        return Response({
            "success": True,
            "data": arr,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_coa(self, request):
        """
        <GET> /api/administration/get_coa
        """
        client = request.user.user_acc.first().client

        acc = core_models.Accounts.objects.filter(
            client=client,
            status=1,
        ).order_by('code')

        arr = []
        if acc:
            for c in acc:
                arr.append({
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                    "parent": c.parent,
                    "type": c.type,
                    "level": c.level
                })

        return Response({
            "success": True,
            "data": arr,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def check_pending(self, request):
        """
        <GET> /api/administration/check_pending
        """
        type = request.query_params.get("type")
        id = int(request.query_params.get("id"))
        client = int(request.query_params.get("client"))

        exist = 0
        type1 = 0
        arr = []

        if int(type) == 1:
            print("Incoming!")
            if id == -1:
                print("All Invoices")
                que = core_models.INCPAY1.objects.filter(
                    inc__code__id=client,
                    inc__status__in=[3, 4]
                )
                if que:
                    exist = 1
                    for qu in que:
                        arr.append(qu.invoice.id)
            else:
                que = core_models.INCPAY1.objects.filter(
                    invoice__id=id,
                    inc__status__in=[3, 4]
                ).first()
                if que:
                    exist = 1
                    arr.append(id)
                    print("Existing!")
                    if que.inc.status == 3:
                        type1 = 1
                    else:
                        type1 = 2
        else:
            if id == -1:
                print("All Invoices")
                que = core_models.OUTPAY1.objects.filter(
                    out__code__id=client,
                    out__status__in=[3, 4]
                )
                if que:
                    exist = 1
                    for qu in que:
                        arr.append(qu.invoice.id)
            else:
                que = core_models.OUTPAY1.objects.filter(
                    invoice__id=id,
                    out__status__in=[3, 4]
                ).first()
                if que:
                    exist = 1
                    arr.append(id)
                    print("Existing!")
                    if que.out.status == 3:
                        type1 = 1
                    else:
                        type1 = 2

        return Response({
            "success": True,
            "exist": exist,
            "type": type1,
            "invs": arr
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_modules(self, request):
        """
        <GET> /api/administration/get_modules
        """
        role = request.query_params.get("role")

        rol = core_models.Roles.objects.filter(id=int(role)).first()

        modules = (
            core_models.Modules.objects
            .values('module')
            .annotate(first_id=Min('id'))
            .order_by('first_id')
        )

        module_records = core_models.Modules.objects.all()

        access_records = core_models.Access.objects.filter(role=rol)

        access_map = {}
        for acc in access_records:
            access_map[acc.module_id] = {
                "id": acc.id,
                "name": acc.module.sub_module,
                "access": acc.access,
                "view": acc.view,
                "create": acc.create,
                "edit": acc.edit,
                "delete": acc.delete
            }

        mod = []

        for m in modules:
            module_name = m["module"]

            lis = []
            for module in module_records:
                if module.module == module_name and module.id in access_map:
                    lis.append(access_map[module.id])

            mod.append({
                "name": module_name,
                "list": lis
            })

        return Response({
            "success": True,
            "data": mod,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_roles1(self, request):
        """
        <GET> /api/administration/get_roles1
        """
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        client = request.query_params.get("client")

        modu = core_models.Roles.objects.all()

        if int(client) != 0:
            modu = modu.filter(client__id=client)
        modu = modu.order_by('id')

        result_page = paginator.paginate_queryset(modu, request)
        serializer = u_ser.RolesSerializer(
            result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def up_roles1(self, request):
        """
        <GET> /api/administration/up_roles1
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        for pd in p_data:
            getRole = core_models.Access.objects.filter(
                id=pd.get("id")
            ).first()
            if getRole:
                getRole.access = pd.get("access")
                getRole.view = pd.get("view")
                getRole.create = pd.get("create")
                getRole.edit = pd.get("edit")
                getRole.delete = pd.get("delete")
                getRole.save()

        return Response({
            "success": True,
            "message": "Successfully updated."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def add_role(self, request):
        """
        <GET> /api/administration/add_role
        """
        data = request.data
        p_data = json.loads(data['datas'])
        print(p_data)

        if int(p_data.get("id")) == 0:
            cli = core_models.Client.objects.filter(
                id=int(p_data.get("client"))).first()
            addR = core_models.Roles(
                client=cli,
                name=p_data.get("name")
            )
            addR.save()

            modu = core_models.Modules.objects.all()
            for module in modu:
                addA = core_models.Access(
                    role=addR,
                    module=module,
                    access=True,
                    view=True,
                    create=False,
                    edit=False,
                    delete=False,
                )
                addA.save()

        else:
            role = core_models.Roles.objects.filter(
                id=int(p_data.get("id"))
            ).first()
            role.name = p_data.get("name")
            role.status = int(p_data.get("status"))
            role.save()

        return Response({
            "success": True,
            "message": "Successfully updated."
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_sidebar(self, request):
        """
        <GET> /api/administration/get_sidebar
        """
        user = request.user.user_acc.first()

        # getRole = core_models.Access.objects.filter(
        #     role=user.role
        # )

        role = core_models.Roles.objects.filter(id=user.role.id).first()

        # modules = (
        #     core_models.Modules.objects
        #     .values('module')
        #     .annotate(first_id=Min('id'))
        #     .order_by('first_id')
        # )

        modules = core_models.Modules.objects.all().values('module').distinct()
        print(f"Module: {list(modules)}")
        arr = []
        i = 1
        for mod in modules:
            access = core_models.Access.objects.filter(
                role=role,
                module__module=mod.get("module")
            )
            j = 0
            for acc in access:
                if acc.view:
                    j += 1
            arr.append({
                "id": i,
                "name": mod.get("module"),
                "access": j
            })
            i += 1

        return Response({
            "success": True,
            "data": arr
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_sidebar_sub(self, request):
        """
        <GET> /api/administration/get_sidebar_sub
        """
        user = request.user.user_acc.first()

        # getRole = core_models.Access.objects.filter(
        #     role=user.role
        # )

        role = core_models.Roles.objects.filter(id=user.role.id).first()

        acc = core_models.Access.objects.filter(
            role=role
        )

        serializer = u_ser.AccessAllSerializer(acc, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def cancel_inc(self, request, pk):
        """
        <GET> /api/administration/id/cancel_inc/
        """
        print(f"PK here: {pk}")
        client = request.user.user_acc.first().client
        jeNo = core_models.DocumentNo.objects.filter(
            client=client,
            name='Journal Entry'
        ).first()
        inc = core_models.INCPAY.objects.filter(
            id=pk
        ).first()
        with transaction.atomic():
            if inc:
                ojdt = core_models.OJDT.objects.filter(
                    origin=6,
                    origin_no=inc.doc_no
                ).first()

                m1 = "Cancellation on Incoming Payment"
                a_ojdt = core_models.OJDT(
                    client=client,
                    no=int(jeNo.no) + 1,
                    origin=6,
                    origin_no=inc.doc_no,
                    remarks=f"{m1} {inc.doc_no}",
                    post_date=timezone.now().date(),
                    due_date=timezone.now().date(),
                    doc_date=timezone.now().date(),
                    trans_no=inc.id,
                    total=ojdt.total
                )
                a_ojdt.save()

                for recs in ojdt.jdt1_rows.all():
                    # print(f"ID here: {recs.id}")
                    super.add_JE(
                        ojdt=a_ojdt,
                        account=recs.account,
                        debit=recs.credit if recs.debit == 0 else 0,
                        credit=recs.debit if recs.credit == 0 else 0,
                        remarks="",
                        post_date=timezone.now().date(),
                        customer=recs.bp.id if recs.bp else ""
                    )

                for invs in inc.incInv.all():
                    invs.invoice.applied_amt -= invs.pay_bal
                    invs.invoice.applied_tax -= invs.pay_tax

                    check_p = core_models.INCPAY1.objects.filter(
                        invoice=invs.invoice,
                        inc__status__in=[1, 6]
                    ).count()
                    if check_p > 1:
                        invs.invoice.status = 2
                    else:
                        invs.invoice.status = 1

                    invs.invoice.save()

                jeNo.no = int(jeNo.no) + 1
                jeNo.save()

                inc.status = 2
                inc.save()

        return Response({
            "success": True,
            "message": "Successfully canceled."
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def cancel_out(self, request, pk):
        """
        <GET> /api/administration/id/cancel_out/
        """
        print(f"PK here: {pk}")
        client = request.user.user_acc.first().client
        jeNo = core_models.DocumentNo.objects.filter(
            client=client,
            name='Journal Entry'
        ).first()
        out = core_models.OUTPAY.objects.filter(
            id=pk
        ).first()
        with transaction.atomic():
            if out:
                ojdt = core_models.OJDT.objects.filter(
                    origin=7,
                    origin_no=out.doc_no
                ).first()

                m1 = "Cancellation on Outgoing Payment"
                a_ojdt = core_models.OJDT(
                    client=client,
                    no=int(jeNo.no) + 1,
                    origin=7,
                    origin_no=out.doc_no,
                    remarks=f"{m1} {out.doc_no}",
                    post_date=timezone.now().date(),
                    due_date=timezone.now().date(),
                    doc_date=timezone.now().date(),
                    trans_no=out.id,
                    total=ojdt.total
                )
                a_ojdt.save()

                for recs in ojdt.jdt1_rows.all():
                    # print(f"ID here: {recs.id}")
                    super.add_JE(
                        ojdt=a_ojdt,
                        account=recs.account,
                        debit=recs.credit if recs.debit == 0 else 0,
                        credit=recs.debit if recs.credit == 0 else 0,
                        remarks="",
                        post_date=timezone.now().date(),
                        customer=recs.bp.id if recs.bp else ""
                    )

                for invs in out.outInv.all():
                    invs.invoice.applied_amt -= invs.pay_bal
                    invs.invoice.applied_tax -= invs.pay_tax

                    check_p = core_models.OUTPAY1.objects.filter(
                        invoice=invs.invoice,
                        out__status__in=[1, 6]
                    ).count()
                    if check_p > 1:
                        invs.invoice.status = 2
                    else:
                        invs.invoice.status = 1

                    invs.invoice.save()

                jeNo.no = int(jeNo.no) + 1
                jeNo.save()

                out.status = 2
                out.save()

        return Response({
            "success": True,
            "message": "Successfully canceled."
        }, status=status.HTTP_200_OK)
