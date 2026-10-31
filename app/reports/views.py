from rest_framework import (
    viewsets,
    status
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core import models as core_models
from django.utils import timezone
from reports import serializers as r_ser
from django.db.models import Q
# from django.db.models.functions import Lower
from app.authentication import CookieJWTAuthentication
# import requests
# from django.conf import settings
# import json
# from django.db import transaction
from django.db.models import (
    Sum, Case, When, F, Value, DecimalField,
    ExpressionWrapper, Prefetch, IntegerField, DurationField
)
from django.utils.timezone import now
from datetime import timedelta, date
from django.db.models.functions import Coalesce, TruncMonth, ExtractDay
from decimal import Decimal
from datetime import datetime
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
import calendar
from core.core_functions import Core as super
import pytz
from rest_framework.pagination import PageNumberPagination


class ReportsView(viewsets.ModelViewSet):
    """
    GET /api/reports
    """
    ph_timezone = timezone.get_fixed_timezone(480)
    current_time_ph = timezone.localtime(
        timezone.now(), ph_timezone)
    queryset = ""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _sum_by_category(self, request, category, fromD, toD, je_ids=None):
        queryset = core_models.JDT1.objects.filter(
            je__client=request.user.user_acc.first().client,
            account__category=category,
            account__status=1,
            post_date__range=[fromD, toD],
        )

        if je_ids is not None:
            queryset = queryset.filter(je_id__in=je_ids)

        return queryset.aggregate(
            amt=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("debit") - F("credit"),
                        output_field=DecimalField(
                            max_digits=20, decimal_places=2),
                    )
                ),
                Decimal("0.00"),
            )
        )["amt"]

    def _get_opening_net_income(self, request, from_date):
        qs = core_models.JDT1.objects.filter(
            je__client=request.user.user_acc.first().client,
            account__category__in=[4, 5, 6, 7],
            account__status=1,
            post_date__lt=from_date,
        ).aggregate(
            amt=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("debit") - F("credit"),
                        output_field=DecimalField(
                            max_digits=20, decimal_places=2),
                    )
                ),
                Decimal("0.00"),
            )
        )

        return -qs["amt"]

    def _get_net_income(self, request, fromD, toD, je_ids=None):
        income = self._sum_by_category(request, 4, fromD, toD, je_ids)
        cogs = self._sum_by_category(request, 5, fromD, toD, je_ids)
        expense = self._sum_by_category(request, 6, fromD, toD, je_ids)
        other = self._sum_by_category(request, 7, fromD, toD, je_ids)

        ni = -income - cogs - expense + -other
        return ni

    def _get_net_income_monthly(self, request, fromD, toD):
        from_date = datetime.strptime(fromD, "%Y-%m-%d")
        to_date = datetime.strptime(toD, "%Y-%m-%d")

        def generate_months(from_date, to_date):
            months = []
            year, month = from_date.year, from_date.month
            while (year, month) <= (to_date.year, to_date.month):
                months.append(f"{year}-{month:02d}")
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            return months

        months = generate_months(from_date, to_date)

        def monthly_sum(category, reverse=False):
            expr = (
                ExpressionWrapper(
                    F("credit") - F("debit"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
                if reverse
                else ExpressionWrapper(
                    F("debit") - F("credit"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )

            qs = (
                core_models.JDT1.objects.filter(
                    je__client=request.user.user_acc.first().client,
                    account__category=category,
                    account__status=1,
                    post_date__range=[from_date, to_date],
                )
                .annotate(month=TruncMonth("post_date"))
                .values("month")
                .annotate(
                    amt=Coalesce(
                        Sum(expr),
                        Decimal("0.00"),
                    )
                )
            )

            return {row["month"].strftime("%Y-%m"): row["amt"] for row in qs}

        income = monthly_sum(4, reverse=True)   # credit - debit
        cogs = monthly_sum(5)
        expense = monthly_sum(6)
        other = monthly_sum(7)

        net_income_monthly_raw = [
            income.get(m, Decimal("0.00"))
            - cogs.get(m, Decimal("0.00"))
            + -expense.get(m, Decimal("0.00"))
            + other.get(m, Decimal("0.00"))
            for m in months
        ]

        # CUMULATIVE (balance-sheet style)
        net_income_cumulative = []
        running_total = Decimal("0.00")

        for amt in net_income_monthly_raw:
            running_total += amt
            net_income_cumulative.append(running_total)

        return net_income_cumulative

    def _get_net_income_monthly1(self, request, fromD, toD):
        from_date = datetime.strptime(fromD, "%Y-%m-%d")
        to_date = datetime.strptime(toD, "%Y-%m-%d")

        # Generate list of months as date objects (1st of each month)
        def generate_months(from_date, to_date):
            months = []
            year, month = from_date.year, from_date.month

            while (year, month) <= (to_date.year, to_date.month):
                months.append(date(year, month, 1))
                month += 1
                if month > 12:
                    month = 1
                    year += 1

            return months

        months = generate_months(from_date, to_date)

        def monthly_sum(category, reverse=False):
            expr = (
                ExpressionWrapper(
                    F("credit") - F("debit"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
                if reverse
                else ExpressionWrapper(
                    F("debit") - F("credit"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )

            qs = (
                core_models.JDT1.objects.filter(
                    je__client=request.user.user_acc.first().client,
                    account__category=category,
                    account__status=1,
                    post_date__range=[from_date, to_date],
                )
                .annotate(month=TruncMonth("post_date"))
                .values("month")
                .annotate(
                    amt=Coalesce(
                        Sum(expr),
                        Decimal("0.00"),
                    )
                )
            )

            # Key = date(YYYY, MM, 01)
            return {row["month"]: row["amt"] for row in qs}

        # Category mappings
        income = monthly_sum(4, reverse=True)   # credit - debit
        cogs = monthly_sum(5)
        expense = monthly_sum(6)
        other = monthly_sum(7)

        net_income_cumulative = []
        running_total = Decimal("0.00")

        for m in months:
            amt = (
                income.get(m, Decimal("0.00"))
                - cogs.get(m, Decimal("0.00"))
                - expense.get(m, Decimal("0.00"))
                + other.get(m, Decimal("0.00"))
            )

            running_total = amt  # per your original logic (not rolling)

            net_income_cumulative.append({
                "month": m.strftime("%b %Y"),
                "value": running_total
            })

        return net_income_cumulative

    def _get_account_total(self, client, category_alias,
                           fromD, toD, reverse=False):
        sign = -1 if reverse else 1

        result = core_models.Accounts.objects.filter(
            category__alias=category_alias,
            client=client
        ).aggregate(
            total=Coalesce(
                Sum(
                    sign * (F('jdt1__debit') - F('jdt1__credit')),
                    filter=Q(jdt1__post_date__range=[fromD, toD]),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )

        return result["total"]

    def _get_bank_account(self, request):
        bank_id = request.query_params.get("bank_id")
        if not bank_id or str(bank_id).strip().lower() == "all":
            return None

        try:
            bank_id = int(bank_id)
        except (TypeError, ValueError):
            raise ValidationError({"bank_id": "Invalid bank_id."})

        client = request.user.user_acc.first().client
        bank = core_models.Accounts.objects.filter(
            id=bank_id,
            client=client,
            cash=True,
            status=1,
        ).first()

        if not bank:
            raise ValidationError({"bank_id": "Bank account not found."})

        return bank

    def _get_bank_scope_ids(self, client, bank):
        if not bank:
            return []

        accounts = core_models.Accounts.objects.filter(
            client=client,
            cash=True,
            status=1,
        ).values("id", "parent")

        children_map = {}
        for account in accounts:
            parent = account["parent"]
            if parent:
                children_map.setdefault(parent, []).append(account["id"])

        bank_scope_ids = []
        stack = [bank.id]
        seen = set()

        while stack:
            account_id = stack.pop()
            if account_id in seen:
                continue

            seen.add(account_id)
            bank_scope_ids.append(account_id)

            for child_id in children_map.get(account_id, []):
                if child_id not in seen:
                    stack.append(child_id)

        return bank_scope_ids

    def _get_account_type_by_bp(self, request, bp_type, paginated=False):
        type = request.query_params.get("type")
        fromD = request.query_params.get("fromD")
        toD = request.query_params.get("toD")
        search = (request.query_params.get("search") or "").strip()
        export_all_raw = request.query_params.get("export_all")
        export_all = (
            str(export_all_raw).lower() in ["1", "true", "yes"]
            if export_all_raw is not None
            else False
        )

        if not type:
            raise ValidationError({
                "type": "This query parameter is required."})
        if not fromD or not toD:
            msg = "Both fromD and toD query parameters are required."
            raise ValidationError({"fromD/toD": msg})

        try:
            from_date = datetime.strptime(fromD, "%Y-%m-%d")
            to_date = datetime.strptime(toD, "%Y-%m-%d")
        except ValueError:
            raise ValidationError({
                "fromD/toD": "Invalid date format, expected YYYY-MM-DD."})

        page = 1
        page_size = 20
        if paginated and not export_all:
            page_raw = request.query_params.get("page") or "1"
            page_size_raw = request.query_params.get("page_size") or "20"

            try:
                page = int(page_raw)
            except (TypeError, ValueError):
                raise ValidationError({"page": "Invalid page."})

            try:
                page_size = int(page_size_raw)
            except (TypeError, ValueError):
                raise ValidationError({"page_size": "Invalid page_size."})

            if page < 1:
                raise ValidationError({"page": "page must be >= 1."})
            if page_size < 1:
                raise ValidationError({"page_size": "page_size must be >= 1."})

            page_size = min(page_size, 100)

        client = request.user.user_acc.first().client

        acct = core_models.Accounts.objects.filter(
            client=client,
            status=1,
            category=int(type)
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    filter=Q(jdt1__post_date__range=[from_date, to_date]),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        ).exclude(Q(type=2) & Q(calc_balance=0)).order_by('id')

        account_ids = list(acct.values_list('id', flat=True))

        all_customers_qs = core_models.BusinessPartner.objects.filter(
            client=client,
            type=bp_type,
            status=1
        ).order_by('id')

        if search:
            all_customers_qs = all_customers_qs.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        total_count = all_customers_qs.count() if paginated else 0
        total_pages = 0
        has_next = False
        has_previous = False

        if paginated:
            if export_all:
                all_customers = list(all_customers_qs)
                page = 1
                page_size = total_count if total_count > 0 else page_size
                total_pages = 1 if total_count > 0 else 0
            else:
                total_pages = (
                    (total_count + page_size - 1) // page_size
                    if total_count
                    else 0
                )

                if total_pages and page > total_pages:
                    all_customers = []
                else:
                    start = (page - 1) * page_size
                    end = start + page_size
                    all_customers = list(all_customers_qs[start:end])

                has_next = total_pages > 0 and page < total_pages
                has_previous = total_pages > 0 and page > 1
        else:
            all_customers = list(all_customers_qs)

        account_cust_map = {acct_id: {} for acct_id in account_ids}
        if account_ids and all_customers:
            customer_ids = [cust.id for cust in all_customers]
            jdt1_agg = (
                core_models.JDT1.objects
                .filter(
                    je__client=client,
                    account_id__in=account_ids,
                    post_date__range=[from_date, to_date],
                    bp_id__in=customer_ids,
                    bp__type=bp_type,
                    bp__status=1,
                    bp__client=client,
                )
                .values('account_id', 'bp')
                .annotate(
                    amount=Coalesce(
                        Sum(F('debit') - F('credit')),
                        0,
                        output_field=DecimalField(
                            max_digits=20, decimal_places=2)
                    )
                )
            )

            for entry in jdt1_agg:
                account_cust_map[entry['account_id']][entry['bp']] = (
                    entry['amount']
                )

        serialized_data = r_ser.Accounts4Serializer(
            acct,
            many=True,
            context={
                'account_cust_map': account_cust_map,
                'all_customers': all_customers,
            }
        ).data

        if not paginated:
            return serialized_data, None

        return serialized_data, {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
        }

    @action(methods=['GET'], detail=False)
    def get_account_type(self, request):
        """
        <GET> /api/reports/get_account_type
        """
        type = request.query_params.get("type")
        fromD = request.query_params.get("fromD")
        toD = request.query_params.get("toD")

        acct = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            status=1,
            category=int(type)
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    filter=Q(jdt1__post_date__range=[fromD, toD]),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        ).exclude(Q(type=2) & Q(calc_balance=0)).order_by('id')

        serialized_data = r_ser.AccountsSerializer(acct, many=True).data

        if int(type) == 3:
            ni = self._get_net_income(request, fromD, toD)
            net_income_account = {
                "id": 0,
                "name": "Net Income",
                "code": "",
                "type": 2,
                "level": 2,
                "category": 3,
                "parent": 151,
                "balance": ni,
            }
            serialized_data.append(net_income_account)

        return Response({
            "success": True,
            "data": serialized_data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_type_cust(self, request):
        """
        <GET> /api/reports/get_account_type_cust
        """
        serialized_data, meta = self._get_account_type_by_bp(
            request,
            bp_type=1,
            paginated=True,
        )

        payload = {
            "success": True,
            "data": serialized_data
        }
        if meta:
            payload.update(meta)

        return Response(payload, status=200)

    @action(methods=['GET'], detail=False)
    def get_account_type_vendor(self, request):
        """
        <GET> /api/reports/get_account_type_vendor
        """
        serialized_data, meta = self._get_account_type_by_bp(
            request,
            bp_type=2,
            paginated=True,
        )

        payload = {
            "success": True,
            "data": serialized_data,
        }
        if meta:
            payload.update(meta)

        return Response(payload, status=200)

    @action(methods=['GET'], detail=False)
    def get_account_type_monthly(self, request):
        """
        <GET> /api/reports/get_account_type_monthly
        """
        type = request.query_params.get("type")
        type1 = request.query_params.get("type1")
        fromD = request.query_params.get("fromD")
        toD = request.query_params.get("toD")

        accounts = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            status=1,
            category=int(type)
        )
        # .exclude(Q(type=2) & Q(balance=0)).order_by('id')

        serializer = r_ser.Accounts1Serializer(
            accounts, many=True, context={'fromD': fromD, 'toD': toD}).data

        if int(type) == 3 and type1 == 3:
            print("Goods")
            ni = self._get_net_income_monthly(request, fromD, toD)
            net_income_account = {
                "id": 0,
                "name": "Net Income",
                "code": "",
                "type": 2,
                "level": 2,
                "category": 3,
                "parent": 151,
                "monthly_balances": ni,
            }
            serializer.append(net_income_account)

        return Response({
            "success": True,
            "data": serializer
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_account_type_monthly_bs(self, request):
        """
        <GET> /api/reports/get_account_type_monthly_bs
        """
        type = request.query_params.get("type")
        fromD = request.query_params.get("fromD")
        toD = request.query_params.get("toD")

        accounts = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            status=1,
            category=int(type)
        )
        # .exclude(Q(type=2) & Q(balance=0)).order_by('id')

        serializer = r_ser.Accounts2Serializer(
            accounts, many=True, context={'fromD': fromD, 'toD': toD}).data

        if int(type) == 3:
            print("Goods")
            ni = self._get_net_income_monthly(request, fromD, toD)
            net_income_account = {
                "id": 0,
                "name": "Net Income",
                "code": "",
                "type": 2,
                "level": 2,
                "category": 3,
                "parent": 151,
                "monthly_balances": ni,
            }
            serializer.append(net_income_account)

        return Response({
            "success": True,
            "data": serializer
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_gen_ledger(self, request):
        """
        <GET> /api/reports/get_gen_ledger
        """
        fromD = parse_date(request.query_params.get("fromD"))
        toD = parse_date(request.query_params.get("toD"))
        acc = int(request.query_params.get("acc"))

        client = request.user.user_acc.first().client

        # Prefetch transactions only once

        jdt1_qs = core_models.JDT1.objects.filter(
            post_date__range=[fromD, toD]
        ).select_related("je", "bp")

        accounts_qs = core_models.Accounts.objects.filter(
            client=client,
            status=1,
            type=2
        )
        if acc != 0:
            accounts_qs = accounts_qs.filter(id=acc)

        accounts = (
            accounts_qs
            .exclude(balance=0)
            .annotate(
                start_balance=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("jdt1__debit") - F("jdt1__credit"),
                            output_field=DecimalField(
                                max_digits=20, decimal_places=2),
                        ),
                        filter=Q(jdt1__post_date__lt=fromD)
                    ),
                    Decimal("0.00")
                )
            )
            .prefetch_related(
                Prefetch("jdt1", queryset=jdt1_qs, to_attr="trans_rows")
            )
            .order_by("id")
        )

        serializer = r_ser.GenLedgerSerializer(accounts, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(methods=['GET'], detail=False)
    def get_journal_report(self, request):
        """
        <GET> /api/reports/get_journal_report
        """
        client = request.user.user_acc.first().client
        fromD = parse_date(request.query_params.get("fromD"))
        toD = parse_date(request.query_params.get("toD"))

        queryset = (
            core_models.JDT1.objects.filter(
                je__client=client,
                post_date__range=(fromD, toD),
            ).select_related(
                "je", "account", "bp",
            )
        ).order_by("-je_id")

        serializer = r_ser.JournalReportSerializer(queryset, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_cash_flow(self, request):
        """
        <GET> /api/reports/get_cash_flow
        """
        client = request.user.user_acc.first().client
        fromD = parse_date(request.query_params.get("fromD"))
        toD = parse_date(request.query_params.get("toD"))
        ni = self._get_net_income(request, fromD, toD)

        ca = core_models.Accounts.objects.filter(
            Q(client=client) &
            Q(status=1) &
            Q(type=2) &
            (
                Q(code__startswith="010102") |
                Q(code__startswith="010103")
            )
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    filter=Q(jdt1__post_date__range=[fromD, toD]),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        ).exclude(Q(calc_balance=0)).order_by('id')

        ca_serialize = r_ser.Accounts3Serializer(ca, many=True).data

        fa = core_models.Accounts.objects.filter(
            Q(client=client) &
            Q(status=1) &
            Q(type=2) &
            (
                Q(code__startswith="0102") |
                Q(code__startswith="0103")
            )
        ).annotate(
            calc_balance=Coalesce(
                Sum(
                    F('jdt1__debit') - F('jdt1__credit'),
                    filter=Q(jdt1__post_date__range=[fromD, toD]),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        ).exclude(Q(calc_balance=0)).order_by('id')

        fa_serialize = r_ser.Accounts3Serializer(fa, many=True).data

        begin_cash = core_models.JDT1.objects.filter(
            account__client=client,
            account__cash=True,
            post_date__lt=fromD
        ).aggregate(
            amt=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("debit") - F("credit"),
                        output_field=DecimalField(
                            max_digits=20, decimal_places=2),
                    )
                ),
                Decimal("0.00"),
            )
        )

        return Response({
            "success": True,
            "ca": ca_serialize,
            "fa": fa_serialize,
            "ni": ni,
            "begin_cash": begin_cash['amt']
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_cash_flow2(self, request):
        """
        <GET> /api/reports/get_cash_flow2
        """
        client = request.user.user_acc.first().client
        fromD = parse_date(request.query_params.get("fromD"))
        toD = parse_date(request.query_params.get("toD"))
        bank = self._get_bank_account(request)

        bank_scope_ids = []
        period_je_ids = None
        if bank:
            bank_scope_ids = self._get_bank_scope_ids(client, bank)
            period_je_ids = core_models.JDT1.objects.filter(
                je__client=client,
                account_id__in=bank_scope_ids,
                post_date__range=[fromD, toD],
            ).values_list("je_id", flat=True).distinct()

        # --------------------------------------------------
        # Generate months
        # --------------------------------------------------
        def generate_months(from_date, to_date):
            months = []
            year, month = from_date.year, from_date.month
            while (year, month) <= (to_date.year, to_date.month):
                months.append(date(year, month, 1))
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            return months

        months = generate_months(fromD, toD)

        # --------------------------------------------------
        # Beginning cash
        # --------------------------------------------------
        begin_cash = core_models.JDT1.objects.filter(
            account__client=client,
            account__cash=True,
            post_date__lt=fromD
        ).aggregate(
            amt=Coalesce(
                Sum(F("debit") - F("credit")),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )["amt"]

        if bank:
            begin_cash = core_models.JDT1.objects.filter(
                account__client=client,
                account_id__in=bank_scope_ids,
                post_date__lt=fromD
            ).aggregate(
                amt=Coalesce(
                    Sum(F("debit") - F("credit")),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )["amt"]

        # --------------------------------------------------
        # Monthly Net Income
        # --------------------------------------------------
        def monthly_net_income():
            def sum_cat(category, reverse=False):
                expr = (
                    F("credit") - F("debit")
                    if reverse
                    else F("debit") - F("credit")
                )

                cat_filter = Q(
                    account__client=client,
                    account__status=1,
                    account__category=category,
                    post_date__range=[fromD, toD],
                )
                if bank:
                    cat_filter &= Q(je_id__in=period_je_ids)

                qs = (
                    core_models.JDT1.objects.filter(cat_filter)
                    .annotate(month=TruncMonth("post_date"))
                    .values("month")
                    .annotate(
                        amt=Coalesce(
                            Sum(expr),
                            Decimal("0.00"),
                            output_field=DecimalField(
                                max_digits=20, decimal_places=2),
                        )
                    )
                )

                return {row["month"]: row["amt"] for row in qs}

            income = sum_cat(4, reverse=True)   # credit - debit
            cogs = sum_cat(5)
            expense = sum_cat(6)
            other = sum_cat(7)

            ni_map = {}
            for m in months:
                ni_map[m] = (
                    income.get(m, Decimal("0.00"))
                    - cogs.get(m, Decimal("0.00"))
                    - expense.get(m, Decimal("0.00"))
                    + other.get(m, Decimal("0.00"))
                )
            return ni_map

        ni_map = monthly_net_income()

        # --------------------------------------------------
        # Current Assets movement (NON-cash)
        # --------------------------------------------------
        ca_filter = (
            Q(account__code__startswith="010102") |
            Q(account__code__startswith="010103")
        ) & Q(
            account__client=client,
            account__status=1,
            account__type=2,
            account__cash=False,
            post_date__range=[fromD, toD],
        )
        if bank:
            ca_filter &= Q(je_id__in=period_je_ids)

        ca_qs = (
            core_models.JDT1.objects.filter(ca_filter)
            .annotate(month=TruncMonth("post_date"))
            .values("month")
            .annotate(
                amt=Coalesce(
                    Sum(F("debit") - F("credit")),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )
        )

        ca_map = {row["month"]: row["amt"] for row in ca_qs}

        # --------------------------------------------------
        # Fixed Assets movement (NON-cash)
        # --------------------------------------------------
        fa_filter = (
            Q(account__code__startswith="0102") |
            Q(account__code__startswith="0103")
        ) & Q(
            account__client=client,
            account__status=1,
            account__type=2,
            account__cash=False,
            post_date__range=[fromD, toD],
        )
        if bank:
            fa_filter &= Q(je_id__in=period_je_ids)

        fa_qs = (
            core_models.JDT1.objects.filter(fa_filter)
            .annotate(month=TruncMonth("post_date"))
            .values("month")
            .annotate(
                amt=Coalesce(
                    Sum(F("debit") - F("credit")),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )
        )

        fa_map = {row["month"]: row["amt"] for row in fa_qs}

        # --------------------------------------------------
        # Build monthly cash flow
        # --------------------------------------------------
        results = []
        running_cash = begin_cash

        for m in months:
            ni_amt = ni_map.get(m, Decimal("0.00"))
            ca_change = ca_map.get(m, Decimal("0.00"))
            fa_change = fa_map.get(m, Decimal("0.00"))

            net_cash_change = ni_amt - ca_change - fa_change

            inflow = max(net_cash_change, Decimal("0.00"))
            outflow = abs(min(net_cash_change, Decimal("0.00")))

            running_cash += net_cash_change

            results.append({
                "mth": m.strftime("%b %Y"),
                "net_income": ni_amt,
                "ca_change": ca_change,
                "fa_change": fa_change,
                "inflow": inflow,
                "outflow": outflow,
                "ending_cash": running_cash,
            })

        return Response({
            "success": True,
            "begin_cash": begin_cash,
            "monthly_cashflow": results
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_cash_flow_monthly(self, request):
        """
        <GET> /api/reports/get_cash_flow_monthly
        Monthly cashflow – inflow / outflow / ending cash
        """
        client = request.user.user_acc.first().client
        fromD = parse_date(request.query_params.get("fromD"))
        toD = parse_date(request.query_params.get("toD"))

        # --------------------------------------------------
        # Generate months
        # --------------------------------------------------
        def generate_months(from_date, to_date):
            months = []
            year, month = from_date.year, from_date.month

            while (year, month) <= (to_date.year, to_date.month):
                months.append(date(year, month, 1))
                month += 1
                if month > 12:
                    month = 1
                    year += 1

            return months

        months = generate_months(fromD, toD)

        # --------------------------------------------------
        # Beginning cash
        # --------------------------------------------------
        begin_cash = core_models.JDT1.objects.filter(
            account__client=client,
            account__cash=True,
            post_date__lt=fromD
        ).aggregate(
            amt=Coalesce(
                Sum(F("debit") - F("credit")),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )["amt"]

        # --------------------------------------------------
        # Monthly inflow / outflow
        # --------------------------------------------------
        cash_qs = (
            core_models.JDT1.objects.filter(
                account__client=client,
                account__cash=True,
                post_date__range=[fromD, toD],
            )
            .annotate(month=TruncMonth("post_date"))
            .values("month")
            .annotate(
                inflow=Coalesce(
                    Sum("debit"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
                outflow=Coalesce(
                    Sum("credit"),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                ),
            )
        )

        monthly_cash = {
            row["month"]: {
                "inflow": row["inflow"],
                "outflow": row["outflow"],
            }
            for row in cash_qs
        }

        # --------------------------------------------------
        # Build monthly cashflow
        # --------------------------------------------------
        results = []
        running_cash = begin_cash

        for m in months:
            inflow = monthly_cash.get(m, {}).get("inflow", Decimal("0.00"))
            outflow = monthly_cash.get(m, {}).get("outflow", Decimal("0.00"))

            running_cash += inflow - outflow

            results.append({
                "mth": m.strftime("%b %Y"),
                "inflow": inflow,
                "outflow": outflow,
                "ending_cash": running_cash,
            })

        return Response({
            "success": True,
            "begin_cash": begin_cash,
            "monthly_cashflow": results
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def print_ar_invoice(self, request, pk):
        """
        <GET> /api/reports/pk/print_ar_invoice
        """
        que = core_models.AROINV.objects.filter(
            id=pk
        ).first()

        serializer = r_ser.InvPrintSerializer(que, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def print_ap_invoice(self, request, pk):
        """
        <GET> /api/reports/pk/print_ap_invoice
        """
        que = core_models.APOINV.objects.filter(
            id=pk
        ).first()

        serializer = r_ser.InvAPPrintSerializer(que, many=False)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_aging_client(self, request):
        """
        <GET> /api/reports/get_ar_aging_client
        """
        today = now().date()

        outstanding = ExpressionWrapper(
            F("total")
            - Coalesce(F("applied_amt"), Value(0))
            - Coalesce(F("applied_tax"), Value(0)),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )

        aging_per_client = (
            core_models.AROINV.objects
            .filter(status__in=[1, 2])
            .values(
                cid=F("code__id"),
                cname=F("code__name")
            )
            .annotate(

                # 0 Days (receipt_date IS NULL)
                a0=Sum(
                    Case(
                        When(Q(receipt_date__isnull=True) |
                             Q(receipt_date__gte=today),
                             then=outstanding),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 1–30 Days
                a1=Sum(
                    Case(
                        When(
                            receipt_date__gte=today - timedelta(days=30),
                            receipt_date__lt=today,
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 31–60 Days
                a2=Sum(
                    Case(
                        When(
                            receipt_date__lt=today - timedelta(days=30),
                            receipt_date__gte=today - timedelta(days=60),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 61–90 Days
                a3=Sum(
                    Case(
                        When(
                            receipt_date__lt=today - timedelta(days=60),
                            receipt_date__gte=today - timedelta(days=90),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 91–120 Days
                a4=Sum(
                    Case(
                        When(
                            receipt_date__lt=today - timedelta(days=90),
                            receipt_date__gte=today - timedelta(days=120),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 121–150 Days
                a5=Sum(
                    Case(
                        When(
                            receipt_date__lt=today - timedelta(days=120),
                            receipt_date__gte=today - timedelta(days=150),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 150+ Days
                a6=Sum(
                    Case(
                        When(
                            receipt_date__lt=today - timedelta(days=150),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),
            )
            .order_by("code__id")
        )

        return Response({
            "success": True,
            "data": aging_per_client
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_aging_invoices(self, request):
        """
        <GET> /api/reports/get_ar_aging_invoices?cid=<pk>
        """
        customer_id = request.query_params.get("cid")

        if not customer_id:
            return Response(
                {"success": False, "message": "customer_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = now().date()

        outstanding = ExpressionWrapper(
            F("total")
            - Coalesce(F("applied_amt"), Value(0))
            - Coalesce(F("applied_tax"), Value(0)),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )

        invoices = (
            core_models.AROINV.objects
            .filter(
                status__in=[1, 2],
                code_id=customer_id
            )
            .annotate(
                days=Case(
                    When(receipt_date__isnull=True, then=Value(0)),
                    When(receipt_date__gt=today, then=Value(0)),
                    default=ExtractDay(
                        ExpressionWrapper(
                            today - F("receipt_date"),
                            output_field=DurationField()
                        )
                    ),
                    output_field=IntegerField()
                ),
                # Aging bucket label per invoice
                aging=Case(
                    When(receipt_date__isnull=True, then=Value("0")),
                    When(
                        receipt_date__gte=today - timedelta(days=30),
                        then=Value("1")),
                    When(
                        receipt_date__gte=today - timedelta(days=60),
                        then=Value("2")),
                    When(
                        receipt_date__gte=today - timedelta(days=90),
                        then=Value("3")),
                    When(
                        receipt_date__gte=today - timedelta(days=120),
                        then=Value("4")),
                    When(
                        receipt_date__gte=today - timedelta(days=150),
                        then=Value("5")),
                    default=Value("6"),
                ),

                balance=outstanding
            )
            .values(
                "id",
                "invoice_num",
                "receipt_date",
                "posting_date",
                "due_date",
                "days",
                "aging",
                "balance",
                "remarks"
            )
            .order_by("receipt_date")
        )

        return Response({
            "success": True,
            "cid": customer_id,
            "data": list(invoices)
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ap_aging_client(self, request):
        """
        <GET> /api/reports/get_ap_aging_client
        """
        today = now().date()

        outstanding = ExpressionWrapper(
            F("total")
            - Coalesce(F("applied_amt"), Value(0))
            - Coalesce(F("applied_tax"), Value(0)),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )

        aging_per_client = (
            core_models.APOINV.objects
            .filter(status__in=[1, 2])
            .values(
                cid=F("code__id"),
                cname=F("code__name")
            )
            .annotate(

                a0=Sum(
                    Case(
                        When(
                            due_date__gte=today,
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 1–30 Days
                a1=Sum(
                    Case(
                        When(
                            due_date__gte=today - timedelta(days=30),
                            due_date__lt=today,
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 31–60 Days
                a2=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=30),
                            due_date__gte=today - timedelta(days=60),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 61–90 Days
                a3=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=60),
                            due_date__gte=today - timedelta(days=90),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 91–120 Days
                a4=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=90),
                            due_date__gte=today - timedelta(days=120),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 121–150 Days
                a5=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=120),
                            due_date__gte=today - timedelta(days=150),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),

                # 150+ Days
                a6=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=150),
                            then=outstanding
                        ),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ),
            )
            .order_by("code__id")
        )

        return Response({
            "success": True,
            "data": aging_per_client
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ap_aging_invoices(self, request):
        """
        <GET> /api/reports/get_ap_aging_invoices?cid=<pk>
        """
        customer_id = request.query_params.get("cid")

        if not customer_id:
            return Response(
                {"success": False, "message": "customer_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = now().date()

        outstanding = ExpressionWrapper(
            F("total")
            - Coalesce(F("applied_amt"), Value(0))
            - Coalesce(F("applied_tax"), Value(0)),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )

        invoices = (
            core_models.APOINV.objects
            .filter(
                status__in=[1, 2],
                code_id=customer_id
            )
            .annotate(
                days=Case(
                    When(due_date__gte=today, then=Value(0)),
                    default=ExtractDay(
                        ExpressionWrapper(
                            today - F("due_date"),
                            output_field=DurationField()
                        )
                    ),
                    output_field=IntegerField()
                ),
                # Aging bucket label per invoice
                aging=Case(
                    When(due_date__gte=today, then=Value("0")),
                    When(
                        due_date__gte=today - timedelta(days=30),
                        then=Value("1")),
                    When(
                        due_date__gte=today - timedelta(days=60),
                        then=Value("2")),
                    When(
                        due_date__gte=today - timedelta(days=90),
                        then=Value("3")),
                    When(
                        due_date__gte=today - timedelta(days=120),
                        then=Value("4")),
                    When(
                        due_date__gte=today - timedelta(days=150),
                        then=Value("5")),
                    default=Value("6"),
                ),

                balance=outstanding
            )
            .values(
                "id",
                "invoice_num",
                "posting_date",
                "due_date",
                "due_date",
                "days",
                "aging",
                "balance",
            )
            .order_by("due_date")
        )

        return Response({
            "success": True,
            "cid": customer_id,
            "data": list(invoices)
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ap_cal(self, request):
        """
        <GET> /api/reports/get_ap_cal?date="2026-01-28"
        """
        client = request.user.user_acc.first().client

        date_r = request.query_params.get("date")

        curr_date = datetime.strptime(date_r, "%Y-%m-%d").date()
        # ---- Previous month ----
        if curr_date.month == 1:
            prev_month = 12
            prev_year = curr_date.year - 1
        else:
            prev_month = curr_date.month - 1
            prev_year = curr_date.year
        p_month = date(prev_year, prev_month, 1)

        # ---- Next month ----
        if curr_date.month == 12:
            next_month = 1
            next_year = curr_date.year + 1
        else:
            next_month = curr_date.month + 1
            next_year = curr_date.year
        n_month = date(
            next_year,
            next_month,
            calendar.monthrange(next_year, next_month)[1]
        )

        ap = core_models.APOINV.objects.filter(
            client=client,
            status__in=[1, 2, 3],
            cancelation=False,
            due_date__range=(p_month, n_month)
        )
        arr = []
        if ap:
            for a in ap:
                arr.append({
                    "id": a.id,
                    "cust": a.bp_name,
                    "rem": a.remarks,
                    "num": a.invoice_num,
                    "due": a.due_date,
                    "bal": a.total - (a.applied_amt + a.applied_tax),
                    "total": a.total,
                    "status": a.status
                })

        return Response({
            "success": True,
            "cal": arr,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_ar_cal(self, request):
        """
        <GET> /api/reports/get_ar_cal?date="2026-01-28"
        """
        client = request.user.user_acc.first().client

        date_r = request.query_params.get("date")

        curr_date = datetime.strptime(date_r, "%Y-%m-%d").date()
        # ---- Previous month ----
        if curr_date.month == 1:
            prev_month = 12
            prev_year = curr_date.year - 1
        else:
            prev_month = curr_date.month - 1
            prev_year = curr_date.year
        p_month = date(prev_year, prev_month, 1)

        # ---- Next month ----
        if curr_date.month == 12:
            next_month = 1
            next_year = curr_date.year + 1
        else:
            next_month = curr_date.month + 1
            next_year = curr_date.year
        n_month = date(
            next_year,
            next_month,
            calendar.monthrange(next_year, next_month)[1]
        )

        ar = core_models.AROINV.objects.filter(
            client=client,
            status__in=[1, 2, 3],
            cancelation=False,
            due_date__range=(p_month, n_month)
        )
        arr = []
        if ar:
            for a in ar:
                arr.append({
                    "id": a.id,
                    "cust": a.bp_name,
                    "rem": a.remarks,
                    "num": a.invoice_num,
                    "due": a.due_date,
                    "bal": a.total - (a.applied_amt + a.applied_tax),
                    "total": a.total,
                    "status": a.status
                })

        return Response({
            "success": True,
            "cal": arr,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_dash1(self, request):
        """
        <GET> /api/reports/get_dash1
        """
        fromD = request.query_params.get("from")
        toD = request.query_params.get("to")
        client = request.user.user_acc.first().client

        assets = self._get_account_total(client, "assets", fromD, toD)
        liabilities = self._get_account_total(client, "liabilities",
                                              fromD, toD, reverse=True)
        income = self._get_account_total(client, "income",
                                         fromD, toD, reverse=True)
        cogs = self._get_account_total(client, "cogs", fromD, toD)
        expense = self._get_account_total(client, "expense", fromD, toD)

        gross = []
        gross.append({
            "name": "Income",
            "value": income,
            "fill": "#22C55E"
        })
        gross.append({
            "name": "COGS",
            "value": cogs,
            "fill": "#1D4ED8"
        })

        net = []
        net.append({
            "name": "Revenue",
            "value": income,
            "fill": "#22C55E"
        })
        net.append({
            "name": "COGS & Expense",
            "value":  cogs + expense,
            "fill": "#1D4ED8"
        })

        invs = []
        open_inv = core_models.AROINV.objects.filter(
            client=client,
            posting_date__range=[fromD, toD],
            status__in=[1, 2],
        )
        paid_inv = core_models.AROINV.objects.filter(
            client=client,
            posting_date__range=[fromD, toD],
            status=3,
            cancelation=False
        )
        invs.append({
            "name": "Paid",
            "value": paid_inv.count(),
            "fill": "#22C55E"
        })
        invs.append({
            "name": "Unpaid",
            "value": open_inv.count(),
            "fill": "#1D4ED8"
        })

        open = core_models.AROINV.objects.filter(
            client=client,
            status__in=[1, 2],
            cancelation=False
        ).aggregate(
            total=Sum(
                F('total') - F('applied_amt') -
                F('applied_tax'), output_field=DecimalField())
        )['total'] or 0

        ni = self._get_net_income_monthly1(request, fromD, toD)

        return Response({
            "success": True,
            "assets": assets,
            "liab": liabilities,
            "gross": gross,
            "grossp": super.round0(
                ((income - cogs) / income) * 100) if income else 0,
            "income": income,
            "cogs": cogs,
            "net": net,
            "netpr": super.round0(((
                (income - cogs - expense) / (income)
                )) * 100) if income and cogs else 0,
            "expense": expense,
            "inv": invs,
            "inv1": super.round0(
                (paid_inv.count() / (paid_inv.count() + open_inv.count()))
                * 100) if paid_inv and open_inv else 0,
            "open_inv": open,
            "ni": ni
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_income_acct(self, request):
        """
        <GET> /api/reports/get_income_acct
        """
        fromD = request.query_params.get("from")
        toD = request.query_params.get("to")

        accounts = core_models.Accounts.objects.filter(
            client=request.user.user_acc.first().client,
            category__alias="income",
            status=1,
        ).exclude(Q(type=2) & Q(balance=0)).order_by('id')

        serializer = r_ser.Accounts1Serializer(
            accounts, many=True, context={'fromD': fromD, 'toD': toD}).data

        return Response({
            "success": True,
            "data": serializer
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_notifications(self, request):
        """
        <GET> /api/reports/get_notifications
        """
        manila_tz = pytz.timezone('Asia/Manila')
        page_size = request.query_params.get("page_size") or 10
        paginator = PageNumberPagination()
        paginator.page_size = page_size

        getNot = core_models.Notifications.objects.filter(
            Q(client=core_models.UserAcc.objects.get(
                user=request.user
            ).client) &
            Q(receiver=request.user.user_acc.first())
        ).order_by('-id')

        arr = []
        id = 1
        notif = 0
        if getNot:
            for getNo in getNot:
                time = getNo.date_added.astimezone(manila_tz)
                arr.append({
                    "id": getNo.id,
                    "message": getNo.message,
                    "site": getNo.module,
                    "read": 1 if getNo.is_read else 2,
                    "date": time.date(),
                    "time": time.time(),
                })
                id += 1

            notif = getNot.filter(is_read=False).count()

        result_page = paginator.paginate_queryset(arr, request)
        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "notif": notif,
            "results": result_page,
        }

        return Response(response_data)

    @action(methods=['PUT'], detail=True)
    def up_notif(self, request, pk=None):
        """
        <GET> /api/reports/up_notif
        """
        if pk == 0 or pk == "0":
            notif = core_models.Notifications.objects.filter(
                client=core_models.UserAcc.objects.get(
                    user=request.user
                ).client
            )
            if notif:
                for noti in notif:
                    noti.is_read = True
                    noti.date_read = datetime.now()
                    noti.type = 1
                    noti.save()
        else:
            notif = core_models.Notifications.objects.filter(id=pk).first()
            if notif:
                notif.is_read = True
                notif.date_read = datetime.now()
                notif.type = 1
                notif.save()

        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_tb(self, request):
        """
        <GET> /api/reports/get_tb
        """
        fromD = request.query_params.get("from")
        toD = request.query_params.get("to")
        client = request.user.user_acc.first().client

        accounts = (
            core_models.Accounts.objects.filter(
                client=client,
                status=1,
            )
            .annotate(
                balance1=Coalesce(
                    Sum(
                        F("jdt1__debit") - F("jdt1__credit"),
                        filter=Q(jdt1__post_date__range=[fromD, toD]),
                        output_field=DecimalField(
                            max_digits=20, decimal_places=2),
                    ),
                    Value(0),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )
            .exclude(balance1=0)
            .values("id", "name", "balance1", "category", "code")
            .order_by("code")
        )

        data = [
            {
                "category": account["category"],
                "code": account["code"],
                "account": account["name"],
                "balance": account["balance1"],
            }
            for account in accounts
        ]

        return Response({
            "success": True,
            "data": data
        }, status=status.HTTP_200_OK)
