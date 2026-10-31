from rest_framework import serializers
from core import models as core_model
from core.core_functions import Core as sf
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from datetime import datetime
from django.db.models import ExpressionWrapper
from decimal import Decimal


def get_opening_balance(account, from_date):
    expr = ExpressionWrapper(
        F('debit') - F('credit'),
        output_field=DecimalField(max_digits=20, decimal_places=2)
    )

    opening = account.jdt1.filter(
        post_date__lt=from_date
    ).aggregate(
        bal=Coalesce(
            Sum(expr),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    )['bal']

    # Reverse sign for liability & equity
    if account.category.id in [2, 3]:
        opening *= -1

    return opening


class AccountsSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance']

    def get_balance(self, obj):
        balance = obj.calc_balance or 0
        if obj.category.id in [2, 3]:
            balance *= -1
        return balance


class Accounts4Serializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    cust = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance', 'cust']

    def get_balance(self, obj):
        balance = obj.calc_balance or 0
        if obj.category.id in [2, 3]:
            balance *= -1
        return balance

    def get_cust(self, obj):
        # Get precomputed mapping from context
        account_cust_map = self.context.get('account_cust_map', {})
        all_customers = self.context.get('all_customers', [])

        # Get mapping for this account
        cust_map = account_cust_map.get(obj.id, {})

        # Include all customers, default amount = 0
        return [{
            "id": cust.id,
            "name": cust.name,
            "amount": cust_map.get(cust.id, 0)
        } for cust in all_customers]


class Accounts3Serializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance']

    def get_balance(self, obj):
        balance = obj.calc_balance or 0
        return balance


class Accounts1Serializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        source='calc_balance',
        read_only=True
    )
    monthly_balances = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance', 'monthly_balances']

    def get_monthly_balances(self, account):
        fromD = self.context.get('fromD')
        toD = self.context.get('toD')

        from_date = datetime.strptime(fromD, "%Y-%m-%d").date()
        to_date = datetime.strptime(toD, "%Y-%m-%d").date()

        # Prepare expression: debit - credit as DecimalField
        expr = ExpressionWrapper(
            F('debit') - F('credit'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )

        # Annotate month and year, then aggregate
        qs = account.jdt1.filter(
            post_date__range=[from_date, to_date]).annotate(
            month=ExtractMonth('post_date'),
            year=ExtractYear('post_date')
        ).values('year', 'month').annotate(
            month_sum=Coalesce(
                Sum(expr),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            )
        )

        # Convert queryset to dictionary for easy lookup
        month_dict = {(item['year'], item['month']):
                      item['month_sum'] for item in qs}

        # Build monthly balances in order
        monthly_sums = []
        current = from_date
        while current <= to_date:
            # last_day = calendar.monthrange(current.year, current.month)[1]
            # end_of_month = min(to_date, datetime(
            #     current.year, current.month, last_day).date())
            val = month_dict.get((current.year, current.month), 0)
            if account.category.id in [2, 3]:
                val *= -1
            monthly_sums.append(val)

            # Next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1).date()
            else:
                current = datetime(current.year, current.month + 1, 1).date()

        return monthly_sums


class Accounts2Serializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        source='calc_balance',
        read_only=True
    )
    monthly_balances = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance', 'monthly_balances']

    def get_monthly_balances(self, account):
        fromD = self.context.get('fromD')
        toD = self.context.get('toD')

        from_date = datetime.strptime(fromD, "%Y-%m-%d").date()
        to_date = datetime.strptime(toD, "%Y-%m-%d").date()

        # Prepare expression: debit - credit as DecimalField
        expr = ExpressionWrapper(
            F('debit') - F('credit'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )

        # Annotate month and year, then aggregate
        qs = account.jdt1.filter(
            post_date__range=[from_date, to_date]).annotate(
            month=ExtractMonth('post_date'),
            year=ExtractYear('post_date')
        ).values('year', 'month').annotate(
            month_sum=Coalesce(
                Sum(expr),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2)
            )
        )

        # Convert queryset to dictionary for easy lookup
        month_dict = {(item['year'], item['month']):
                      item['month_sum'] for item in qs}

        running_total = get_opening_balance(account, from_date)

        # Build monthly balances in order
        monthly_balances = []
        current = from_date
        while current <= to_date:

            val = month_dict.get(
                (current.year, current.month), Decimal("0.00"))

            # Reverse sign for liability & equity
            if account.category.id in [2, 3]:
                val *= -1

            running_total += val
            monthly_balances.append(running_total)

            # Next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1).date()
            else:
                current = datetime(current.year, current.month + 1, 1).date()

        # return monthly_sums
        return monthly_balances


class GenLedgerSerializer(serializers.ModelSerializer):
    start = serializers.DecimalField(
        source="start_balance",
        max_digits=20,
        decimal_places=2,
        read_only=True
    )
    trans = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = [
            "id", "name", "code", "parent",
            "type", "level", "start", "trans"
        ]

    def get_trans(self, obj):
        trans = sorted(
            getattr(obj, "trans_rows", []),
            key=lambda act: act.post_date,
            reverse=False,
        )
        result = []

        for act in trans:
            # get the other rows in the same journal entry
            other_rows = act.je.jdt1_rows.exclude(id=act.id)

            # if current row is debit, get other debit rows
            if act.debit > 0:
                split_accounts = other_rows.filter(debit__gt=0)
            else:
                split_accounts = other_rows.filter(credit__gt=0)

            split = ", ".join(
                row.account.name
                for row in split_accounts
            )

            result.append({
                "id": act.id,
                "type": act.je.get_origin_display(),
                "date": act.post_date,
                "num": act.je.no,
                "name": act.bp.name if act.bp else "",
                "memo": act.remarks,
                "split": split,
                "debit": act.debit,
                "credit": act.credit,
                "amt": act.debit - act.credit,
            })

        return result

        # return [
        #     {
        #         "id": act.id,
        #         "type": act.je.get_origin_display(),
        #         "date": act.post_date,
        #         "num": act.je.no,
        #         "name": act.bp.name if act.bp else "",
        #         "memo": act.remarks,
        #         "split": "-SPLIT-",
        #         "debit": act.debit,
        #         "credit": act.credit,
        #         "amt": act.debit - act.credit,
        #     }
        #     for act in trans
        # ]


class JournalReportSerializer(serializers.ModelSerializer):
    no = serializers.CharField(source="je.no")
    type = serializers.CharField(source="je.get_origin_display")
    origin = serializers.CharField(source="je.origin_no")
    account = serializers.CharField(source="account.name")
    bp = serializers.SerializerMethodField()
    # trans = serializers.SerializerMethodField()

    class Meta:
        model = core_model.JDT1
        fields = [
            "id", "no", "type", "post_date", "origin", "bp",
            "remarks", "account", "debit", "credit"
        ]

    def get_bp(self, obj):
        return obj.bp.name if obj.bp_id else ""


class InvPrintSerializer(serializers.ModelSerializer):
    cicon = serializers.CharField(source="client.logo.url")
    cname = serializers.CharField(source="client.client_name")
    ctin = serializers.CharField(source="client.tin")
    cadd = serializers.CharField(source="client.address")
    cadd1 = serializers.CharField(source="client.address1")
    inv_num = serializers.CharField(source="invoice_num")
    bname = serializers.CharField(source="code.name")
    btin = serializers.CharField(source="code.tin")
    badd = serializers.SerializerMethodField()
    inv_date = serializers.CharField(source="posting_date")
    inv_terms = serializers.CharField(source="code.terms")
    inv_due = serializers.CharField(source="due_date")
    inv_po = serializers.CharField(source="po_num")

    inv_subtotal = serializers.CharField(source="price_bef_vat")
    inv_vat = serializers.CharField(source="vat")
    inv_total = serializers.CharField(source="total")
    inv_balance = serializers.CharField(source="total")

    inv_prep = serializers.CharField(read_only=True)
    inv_prep1 = serializers.SerializerMethodField()
    inv_ver = serializers.CharField(read_only=True)
    inv_ver1 = serializers.SerializerMethodField()
    inv_app = serializers.CharField(read_only=True)
    inv_app1 = serializers.SerializerMethodField()

    terms_client = serializers.CharField(source="client.client_name")
    terms_bname = serializers.SerializerMethodField()
    terms_bacct = serializers.SerializerMethodField()
    terms_no = serializers.SerializerMethodField()
    terms_swift = serializers.SerializerMethodField()

    rows = serializers.SerializerMethodField()

    class Meta:
        model = core_model.AROINV
        fields = ['cicon', 'cname', 'ctin', 'cadd', 'cadd1',
                  'inv_num', 'bname', 'btin', 'badd',
                  'inv_date', 'inv_terms', 'inv_due', 'inv_po',
                  'inv_subtotal', 'inv_vat', 'inv_total',
                  'inv_balance', 'inv_prep', 'inv_prep1',
                  'inv_ver', 'inv_ver1', 'inv_app', 'inv_app1',
                  'terms_client', 'terms_bname', 'terms_bacct',
                  'terms_no', 'terms_swift', 'rows'
                  ]

    def get_badd(self, obj):
        add = core_model.BPAddress.objects.filter(
            bp=obj.code
        ).first()
        if add:
            a1 = add.street
            a2 = (add.barangay.name or "").title()
            a3 = (add.barangay.municipality.name or "").title()
            a4 = (add.barangay.municipality.province.name or "").title()
            return f"{a1}, {a2}, {a3}, {a4}"

    def get_inv_prep1(self, obj):
        return obj.added.job_position if obj.added else ""

    def get_inv_ver1(self, obj):
        return obj.verified.job_position if obj.verified else ""

    def get_inv_app1(self, obj):
        return obj.approved.job_position if obj.approved else ""

    def get_terms_bname(self, obj):
        return obj.code.p_terms.bank_name if obj.code.p_terms else ""

    def get_terms_bacct(self, obj):
        return obj.code.p_terms.acc_name if obj.code.p_terms else ""

    def get_terms_no(self, obj):
        return obj.code.p_terms.acc_no if obj.code.p_terms else ""

    def get_terms_swift(self, obj):
        return obj.code.p_terms.swift_code if obj.code.p_terms else ""

    def get_rows(self, obj):
        inv1 = core_model.ARINV1.objects.filter(
            ar=obj
        )
        arr = []
        for inv in inv1:
            arr.append({
                "id": inv.id,
                "desc": inv.description,
                "rate": inv.amount,
                "amount": inv.amount
            })
        return arr


class InvAPPrintSerializer(serializers.ModelSerializer):
    cicon = serializers.CharField(source="client.logo.url")
    cname = serializers.CharField(source="client.client_name")
    ctin = serializers.CharField(source="client.tin")
    cadd = serializers.CharField(source="client.address")
    cadd1 = serializers.CharField(source="client.address1")
    inv_num = serializers.CharField(source="invoice_num")
    bname = serializers.CharField(source="code.name")
    inv_date = serializers.CharField(source="posting_date")
    inv_remarks = serializers.CharField(source="remarks")
    inv_total = serializers.SerializerMethodField()

    inv_prep = serializers.CharField(read_only=True)
    inv_prep1 = serializers.SerializerMethodField()
    inv_ver = serializers.CharField(read_only=True)
    inv_ver1 = serializers.SerializerMethodField()
    inv_app = serializers.CharField(read_only=True)
    inv_app1 = serializers.SerializerMethodField()

    rows = serializers.SerializerMethodField()

    class Meta:
        model = core_model.APOINV
        fields = ['cicon', 'cname', 'ctin', 'cadd', 'cadd1',
                  'inv_num', 'bname', 'inv_date', 'inv_total',
                  'inv_remarks', 'inv_prep', 'inv_prep1', 'inv_ver',
                  'inv_ver1', 'inv_app', 'inv_app1', 'rows']

    def get_inv_total(self, obj):
        return sf.round2(obj.total) - sf.round2(obj.wtax)

    def get_inv_prep1(self, obj):
        return obj.added.job_position if obj.added else ""

    def get_inv_ver1(self, obj):
        return obj.verified.job_position if obj.verified else ""

    def get_inv_app1(self, obj):
        return obj.approved.job_position if obj.approved else ""

    def get_rows(self, obj):
        inv1 = core_model.JDT1.objects.filter(
            je__origin=4,
            je__origin_no=obj.invoice_num
        )
        arr = []
        for inv in inv1:
            arr.append({
                "id": inv.id,
                "account": inv.account.name,
                "memo": inv.remarks,
                "debit": inv.debit,
                "credit": inv.credit
            })
        return arr


class TrialBalanceSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'category', 'code', 'name', 'parent',
                  'type', 'level', 'balance']

    def get_balance(self, obj):
        balance = obj.calc_balance or 0
        if obj.category.id in [2, 3]:
            balance *= -1
        return balance
