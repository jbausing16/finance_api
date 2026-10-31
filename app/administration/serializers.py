from rest_framework import serializers
from core import models as core_model
from core.core_functions import Core as sf
from datetime import date
from decimal import Decimal
from django.db.models import Sum, DecimalField
# from django.db import transaction
# from django.contrib.auth.hashers import make_password


# class AccountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = core_model.UserAcc
#         fields = '__all__'

class AccCategSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.AccCateg
        fields = ['id', 'name']


class AccountsSerializer(serializers.ModelSerializer):
    account = serializers.CharField(source="name")
    acc_type = serializers.CharField(source="category.id")
    # amount = serializers.CharField(source="balance")
    amount = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = [
            'id',
            'code',
            'account',
            'parent',
            'acc_type',
            'type',
            'level',
            'amount',
            'cash',
            'wtax',
            'status',
            'check_no'
        ]

    def get_amount(self, obj):
        balance = obj.calc_balance or 0
        return balance


class AccountsAllSerializer(serializers.ModelSerializer):
    account = serializers.CharField(source="name")
    acc_type = serializers.CharField(source="category.id")

    class Meta:
        model = core_model.Accounts
        fields = [
            'id',
            'code',
            'account',
            'parent',
            'acc_type',
            'type',
            'level',
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Roles
        fields = ['id', 'name']


class TypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Types
        fields = ['id', 'name']


class ClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="client_name")

    class Meta:
        model = core_model.Client
        fields = ['id', 'name']


# class UserCreateSerializer(serializers.Serializer):
#     # Data fields (from your JSON)
#     email = serializers.EmailField()
#     fname = serializers.CharField(max_length=150)
#     lname = serializers.CharField(max_length=150)
#     username = serializers.CharField(max_length=150)
#     password = serializers.CharField(write_only=True)

#     phone = serializers.CharField(max_length=50, required=False)
#     position = serializers.CharField(max_length=150, required=False)

#     client = serializers.IntegerField()
#     type = serializers.IntegerField()
#     role = serializers.IntegerField()

#     # File fields
#     profile = serializers.ImageField(required=False)
#     sign = serializers.ImageField(required=False)

#     def validate(self, attrs):
#         # Ensure related objects exist
#         attrs["client_obj"] = core_model.Client.objects.get(
#           id=attrs["client"])
#         attrs["type_obj"] = core_model.Types.objects.get(id=attrs["type"])
#         attrs["role_obj"] = core_model.Roles.objects.get(id=attrs["role"])
#         return attrs

#     @transaction.atomic
#     def create(self, validated):
#         # Create User
#         user = core_model.User.objects.create(
#             email=validated["email"],
#             first_name=validated["fname"],
#             last_name=validated["lname"],
#             username=validated["username"],
#             password=make_password(validated["password"]),
#         )

#         # Create UserAcc
#         acc = core_model.UserAcc.objects.create(
#             user=user,
#             client=validated["client_obj"],
#             phone=validated.get("phone"),
#             user_type=validated["type_obj"],
#             job_position=validated.get("position"),
#             role=validated["role_obj"],
#             profile=validated.get("profile"),
#             signature=validated.get("sign"),
#         )

#         return user


class UserSerializer(serializers.ModelSerializer):
    position = serializers.CharField(source="job_position")
    email = serializers.CharField(source="user.email")
    username = serializers.CharField(source="user.username")
    image = serializers.SerializerMethodField()
    signature = serializers.SerializerMethodField()
    # client = serializers.CharField(source="client.client_name")
    role = serializers.CharField(source="role.id")
    type = serializers.IntegerField(source="user_type.id")
    fname = serializers.CharField(source="user.first_name")
    lname = serializers.CharField(source="user.last_name")

    class Meta:
        model = core_model.UserAcc
        fields = [
            'id',
            'position',
            'email',
            'username',
            'image',
            'signature',
            'client',
            'role',
            'type',
            'status',
            'fname',
            'lname',
            'phone'
        ]

    def get_image(self, obj):
        if obj.profile:
            return obj.profile.url
        return ""

    def get_signature(self, obj):
        if obj.signature:
            return obj.signature.url
        return ""


class UserClientSerializer(serializers.ModelSerializer):
    fname = serializers.CharField(source="user.first_name")
    lname = serializers.CharField(source="user.last_name")

    class Meta:
        model = core_model.UserAcc
        fields = [
            'id',
            'fname',
            'lname'
        ]


class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Approval
        fields = '__all__'


class AutoEntriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.AutoEntries
        fields = '__all__'


class PostPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.PostingPeriod
        fields = '__all__'


class ARPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.PaymentTermsAR
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Region
        fields = [
            'id',
            'name'
        ]


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Province
        fields = [
            'id',
            'name'
        ]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Municipality
        fields = [
            'id',
            'name'
        ]


class BarangaySerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Barangay
        fields = [
            'id',
            'name'
        ]


class BPSerializer(serializers.ModelSerializer):
    tax = serializers.IntegerField(source="tax_stat")
    tandc = serializers.PrimaryKeyRelatedField(
        queryset=core_model.PaymentTermsAR.objects.all(),
        source="p_terms"
    )
    wtax = serializers.PrimaryKeyRelatedField(
        queryset=core_model.Accounts.objects.all()
    )

    street = serializers.SerializerMethodField()
    barangay = serializers.SerializerMethodField()
    zipcode = serializers.SerializerMethodField()
    c_person = serializers.SerializerMethodField()
    c_no = serializers.SerializerMethodField()
    c_email = serializers.SerializerMethodField()

    con_type = serializers.SerializerMethodField()
    con_start = serializers.SerializerMethodField()
    con_end = serializers.SerializerMethodField()
    con_person = serializers.SerializerMethodField()
    con_con = serializers.SerializerMethodField()
    con_email = serializers.SerializerMethodField()

    tin = serializers.SerializerMethodField()

    bp_address = serializers.SerializerMethodField()

    class Meta:
        model = core_model.BusinessPartner
        fields = [
            'id', 'type', 'code', 'name', 'tin', 'terms', 'wtax',
            'tax', 'tandc', 'street', 'barangay', 'zipcode',
            'c_person', 'c_no', 'c_email',
            'con_type', 'con_start', 'con_end',
            'con_person', 'con_con', 'con_email',
            'status', 'bp_address'
        ]

    def _address(self, obj):
        return obj.bp_address.first()

    def _contract(self, obj):
        return obj.bp_contract.first()

    def get_tin(self, obj):
        return obj.tin or ""

    def get_street(self, obj):
        addr = self._address(obj)
        return addr.street if addr and addr.street else ""

    def get_barangay(self, obj):
        addr = self._address(obj)
        return addr.barangay.id if addr and addr.barangay else 0

    def get_zipcode(self, obj):
        addr = self._address(obj)
        return addr.zipcode or ""

    def get_c_person(self, obj):
        addr = self._address(obj)
        return addr.c_person or ""

    def get_c_no(self, obj):
        addr = self._address(obj)
        return addr.c_no or ""

    def get_c_email(self, obj):
        addr = self._address(obj)
        return addr.email or ""

    def get_con_type(self, obj):
        con = self._contract(obj)
        return int(con.type) if con and con.type else 0

    def get_con_start(self, obj):
        con = self._contract(obj)
        return con.start_date or ""

    def get_con_end(self, obj):
        con = self._contract(obj)
        return con.end_date or ""

    def get_con_person(self, obj):
        con = self._contract(obj)
        return con.c_person or ""

    def get_con_con(self, obj):
        con = self._contract(obj)
        return con.c_no or ""

    def get_con_email(self, obj):
        con = self._contract(obj)
        return con.email or ""

    def get_bp_address(self, obj):
        addr = self._address(obj)
        arr = [{
            "regionId": 0,
            "provinceId": 0,
            "cityId": 0,
            "barangayId": 0,
            "barangayName": "",
        }]

        if addr and addr.barangay:
            barangay = core_model.Barangay.objects.filter(
                id=addr.barangay.id).first()
            if barangay:
                arr[0] = {
                    "regionId": barangay.municipality.province.region.id,
                    "provinceId": barangay.municipality.province.id,
                    "cityId": barangay.municipality.id,
                    "barangayId": barangay.id,
                    "barangayName": barangay.name,
                }

        return arr

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep['tandc'] = rep.get('tandc') or 0
        rep['wtax'] = rep.get('wtax') or 0

        return rep


class DocNoSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.DocumentNo
        fields = '__all__'


class BPCustSerializer(serializers.ModelSerializer):
    wtax = serializers.PrimaryKeyRelatedField(
        queryset=core_model.AutoEntries.objects.all()
    )
    c_person = serializers.SerializerMethodField()
    c_person = serializers.SerializerMethodField()

    class Meta:
        model = core_model.BusinessPartner
        fields = ['id', 'code', 'name', 'terms',
                  'wtax', 'tax_stat', 'c_person']

    def get_c_person(self, obj):
        per = core_model.BPAddress.objects.get(bp=obj)
        return per.c_person if per else ""

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep['wtax'] = rep.get('wtax') or 0

        return rep


class WtaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.AutoEntries
        fields = '__all__'


class AccountCustSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Accounts
        fields = ['id', 'code', 'type', 'name']


class AccountCust1Serializer(serializers.ModelSerializer):
    child = serializers.SerializerMethodField()

    class Meta:
        model = core_model.Accounts
        fields = ['id', 'code', 'type', 'name', 'level', 'child']

    def get_child(self, obj):
        # `children_map` is passed in context for recursion
        children_map = self.context.get('children_map', {})
        children = children_map.get(obj.id, [])
        return AccountCust1Serializer(children,
                                      many=True,
                                      context=self.context).data


class ARSerializer(serializers.ModelSerializer):
    no = serializers.CharField(source="invoice_num")
    date = serializers.CharField(source="posting_date")
    due = serializers.CharField(source="due_date")
    po = serializers.CharField(source="po_num")
    customer = serializers.CharField(source="bp_name")

    total = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = core_model.AROINV
        fields = ['id', 'no', 'date', 'due', 'status', 'po',
                  'customer', 'balance', 'total']

    def get_total(self, obj):
        cm = core_model.AROCRM.objects.filter(
            ar=obj
        ).aggregate(
            total=Sum('total', output_field=DecimalField())
        )['total'] or 0
        return obj.total - cm

    def get_balance(self, obj):
        apa = obj.applied_amt if obj.applied_amt else 0
        apt = obj.applied_tax if obj.applied_tax else 0
        # cm = core_model.AROCRM.objects.filter(
        #     ar=obj
        # ).aggregate(
        #     total=Sum('total', output_field=DecimalField())
        # )['total'] or 0
        if obj.status > 2:
            return 0
        else:
            return obj.total - apa - apt


class InvSerializer(serializers.ModelSerializer):
    cid = serializers.IntegerField(source="code.id")
    ccode = serializers.CharField(source="bp_code")
    cname = serializers.CharField(source="bp_name")
    cperson = serializers.SerializerMethodField()
    c_terms = serializers.IntegerField(source="code.terms")
    c_wtax = serializers.SerializerMethodField()
    c_tax_stat = serializers.IntegerField(source="code.tax_stat")
    po = serializers.CharField(source="po_num")
    invoice = serializers.CharField(source="invoice_num")
    post_date = serializers.CharField(source="posting_date")
    pricebefvat = serializers.CharField(source="price_bef_vat")
    appliedAmount = serializers.SerializerMethodField()
    rows = serializers.SerializerMethodField()
    wtax1 = serializers.SerializerMethodField()
    taxable = serializers.SerializerMethodField()
    vatable = serializers.SerializerMethodField()

    class Meta:
        model = core_model.AROINV
        fields = [
            'type',
            'cid',
            'ccode',
            'cname',
            'cperson',
            'c_terms',
            'c_wtax',
            'c_tax_stat',
            'po',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'receipt_date',
            'remarks',
            'pricebefvat',
            'discount',
            'vat',
            'wtax',
            'total',
            'appliedAmount',
            'status',
            'rows',
            'wtax1',
            'type',
            'taxable',
            'vatable',
            'cancelation'
        ]

    def get_cperson(self, obj):
        badd = core_model.BPAddress.objects.filter(
            bp=obj.code
        ).first()
        return badd.c_person

    def get_c_wtax(self, obj):
        badd = core_model.BusinessPartner.objects.filter(
            id=obj.code.id
        ).first()
        return badd.wtax.id if badd.wtax else 0

    def get_appliedAmount(self, obj):
        return obj.applied_amt + obj.applied_tax

    def get_rows(self, obj):
        arr = []
        badd = core_model.ARINV1.objects.filter(
            ar=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "description": bad.description,
                "account": str(bad.account.id) if bad.account else 0,
                "customer": str(bad.customer.id) if bad.customer else 0,
                "vatable": bad.vatable,
                "wtax": bad.wtax,
                "discount": bad.discount,
                "amount": bad.amount,
                "product": bad.product.id if bad.product else 0,
                "income": str(bad.account.id) if bad.account else 0,
                "price": bad.price,
                "qty": bad.qty,
            })
            id += 1
        return arr

    def get_wtax1(self, obj):
        arr = []
        badd = core_model.ARINV2.objects.filter(
            ar=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "code": str(bad.wtax.id),
                "name": str(bad.wtax.id),
                "tax_amt": bad.taxable_amt,
                "wtax_amt": bad.wtax_amt,
            })
            id += 1
        return arr

    def get_taxable(self, obj):
        if obj.code.tax_stat == 1:
            return 1
        else:
            return 2

    def get_vatable(self, obj):
        if obj.code.wtax:
            return 1
        else:
            return 2

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # rep['c_wtax'] = rep.get('c_wtax') or 0

        return rep


class InvAPSerializer(serializers.ModelSerializer):
    cid = serializers.IntegerField(source="code.id")
    ccode = serializers.CharField(source="bp_code")
    cname = serializers.CharField(source="bp_name")
    cperson = serializers.SerializerMethodField()
    c_terms = serializers.IntegerField(source="code.terms")
    c_wtax = serializers.SerializerMethodField()
    c_tax_stat = serializers.IntegerField(source="code.tax_stat")
    po = serializers.CharField(source="po_num")
    invoice = serializers.CharField(source="invoice_num")
    post_date = serializers.CharField(source="posting_date")
    pricebefvat = serializers.CharField(source="price_bef_vat")
    appliedAmount = serializers.SerializerMethodField()
    rows = serializers.SerializerMethodField()
    wtax1 = serializers.SerializerMethodField()

    class Meta:
        model = core_model.APOINV
        fields = [
            'cid',
            'ccode',
            'cname',
            'cperson',
            'c_terms',
            'c_wtax',
            'c_tax_stat',
            'po',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'remarks',
            'pricebefvat',
            'discount',
            'vat',
            'wtax',
            'total',
            'appliedAmount',
            'status',
            'rows',
            'wtax1',
            'type',
            'cancelation'
        ]

    def get_cperson(self, obj):
        badd = core_model.BPAddress.objects.filter(
            bp=obj.code
        ).first()
        return badd.c_person

    def get_c_wtax(self, obj):
        badd = core_model.BusinessPartner.objects.filter(
            id=obj.code.id
        ).first()
        return badd.wtax.id if badd.wtax else 0

    def get_rows(self, obj):
        arr = []
        badd = core_model.APINV1.objects.filter(
            ap=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "description": bad.description,
                "account": str(bad.account.id) if bad.account else 0,
                "customer": str(bad.customer.id) if bad.customer else 0,
                "vatable": bad.vatable,
                "wtax": bad.wtax,
                "discount": bad.discount,
                "amount": bad.amount,
                "product": bad.product.id if bad.product else 0,
                "income": str(bad.account.id) if bad.account else 0,
                "price": bad.price,
                "qty": bad.qty,
            })
            id += 1
        return arr

    def get_wtax1(self, obj):
        app = []
        badd = core_model.APINV2.objects.filter(
            ap=obj
        )
        id = 1
        for bad in badd:
            app.append({
                "id": id,
                "code": str(bad.wtax.id),
                "name": str(bad.wtax.id),
                "tax_amt": bad.taxable_amt,
                "wtax_amt": bad.wtax_amt,
            })
            id += 1
        return app

    def get_appliedAmount(self, obj):
        amt = obj.applied_amt or Decimal(0)
        tax = obj.applied_tax or Decimal(0)
        return amt + tax

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # rep['c_wtax'] = rep.get('c_wtax') or 0

        return rep


class JESerializer(serializers.ModelSerializer):
    rows = serializers.SerializerMethodField()
    origin = serializers.CharField(source="get_origin_display")

    class Meta:
        model = core_model.OJDT
        fields = [
            'id',
            'no',
            'origin',
            'origin_no',
            'remarks',
            'post_date',
            'due_date',
            'doc_date',
            'trans_no',
            'total',
            'status',
            'client',
            'rows'
        ]

    def get_rows(self, obj):
        arr = []
        jdt1 = core_model.JDT1.objects.filter(
            je=obj
        ).order_by("id")
        id = 1
        for jdt in jdt1:
            arr.append({
                "id": id,
                "account": str(jdt.account.id),
                "code": jdt.code,
                "name": jdt.name,
                "debit": jdt.debit,
                "credit": jdt.credit,
                "customer": jdt.bp.name if jdt.bp else "",
                "remarks": jdt.remarks,
                "post_date": jdt.post_date
            })
            id += 1
        return arr


class ARCMSerializer(serializers.ModelSerializer):
    ar = serializers.CharField(source="ar.invoice_num")
    no = serializers.CharField(source="invoice_num")
    date = serializers.CharField(source="posting_date")
    customer = serializers.CharField(source="bp_name")

    class Meta:
        model = core_model.AROCRM
        fields = ['id', 'ar', 'no', 'date', 'status',
                  'customer', 'total']


class APCMSerializer(serializers.ModelSerializer):
    ap = serializers.CharField(source="ap.invoice_num")
    no = serializers.CharField(source="invoice_num")
    date = serializers.CharField(source="posting_date")
    vendor = serializers.CharField(source="bp_name")

    class Meta:
        model = core_model.APOCRM
        fields = ['id', 'ap', 'no', 'date', 'status',
                  'vendor', 'total']


class CMSerializer(serializers.ModelSerializer):
    cid = serializers.IntegerField(source="code.id")
    ccode = serializers.CharField(source="bp_code")
    cname = serializers.CharField(source="bp_name")
    cperson = serializers.SerializerMethodField()
    c_terms = serializers.IntegerField(source="code.terms")
    c_wtax = serializers.SerializerMethodField()
    c_tax_stat = serializers.IntegerField(source="code.tax_stat")
    po = serializers.CharField(source="po_num")
    invoice = serializers.CharField(source="invoice_num")
    post_date = serializers.CharField(source="posting_date")
    pricebefvat = serializers.CharField(source="price_bef_vat")
    appliedAmount = serializers.CharField(source="applied_amt")
    rows = serializers.SerializerMethodField()
    wtax1 = serializers.SerializerMethodField()

    class Meta:
        model = core_model.AROCRM
        fields = [
            'cid',
            'ccode',
            'cname',
            'cperson',
            'c_terms',
            'c_wtax',
            'c_tax_stat',
            'po',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'remarks',
            'pricebefvat',
            'discount',
            'vat',
            'wtax',
            'total',
            'appliedAmount',
            'status',
            'rows',
            'wtax1',
            'type',
        ]

    def get_cperson(self, obj):
        badd = core_model.BPAddress.objects.filter(
            bp=obj.code
        ).first()
        return badd.c_person

    def get_c_wtax(self, obj):
        badd = core_model.BusinessPartner.objects.filter(
            id=obj.code.id
        ).first()
        return badd.wtax.id if badd.wtax else 0

    def get_rows(self, obj):
        arr = []
        badd = core_model.ARCRM1.objects.filter(
            ar=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "description": bad.description,
                "account": str(bad.account.id),
                "customer": str(bad.customer.id),
                "vatable": bad.vatable,
                "wtax": bad.wtax,
                "discount": bad.discount,
                "amount": bad.amount
            })
            id += 1
        return arr

    def get_wtax1(self, obj):
        arr = []
        badd = core_model.ARCRM2.objects.filter(
            ar=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "code": str(bad.wtax.id),
                "name": str(bad.wtax.id),
                "tax_amt": bad.taxable_amt,
                "wtax_amt": bad.wtax_amt,
            })
            id += 1
        return arr

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # rep['c_wtax'] = rep.get('c_wtax') or 0

        return rep


class CMAPSerializer(serializers.ModelSerializer):
    cid = serializers.IntegerField(source="code.id")
    ccode = serializers.CharField(source="bp_code")
    cname = serializers.CharField(source="bp_name")
    cperson = serializers.SerializerMethodField()
    c_terms = serializers.IntegerField(source="code.terms")
    c_wtax = serializers.SerializerMethodField()
    c_tax_stat = serializers.IntegerField(source="code.tax_stat")
    po = serializers.CharField(source="po_num")
    invoice = serializers.CharField(source="invoice_num")
    post_date = serializers.CharField(source="posting_date")
    pricebefvat = serializers.CharField(source="price_bef_vat")
    appliedAmount = serializers.CharField(source="applied_amt")
    rows = serializers.SerializerMethodField()
    wtax1 = serializers.SerializerMethodField()

    class Meta:
        model = core_model.APOCRM
        fields = [
            'cid',
            'ccode',
            'cname',
            'cperson',
            'c_terms',
            'c_wtax',
            'c_tax_stat',
            'po',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'remarks',
            'pricebefvat',
            'discount',
            'vat',
            'wtax',
            'total',
            'appliedAmount',
            'status',
            'rows',
            'wtax1',
            'type'
        ]

    def get_cperson(self, obj):
        badd = core_model.BPAddress.objects.filter(
            bp=obj.code
        ).first()
        return badd.c_person

    def get_c_wtax(self, obj):
        badd = core_model.BusinessPartner.objects.filter(
            id=obj.code.id
        ).first()
        return badd.wtax.id if badd.wtax else 0

    def get_rows(self, obj):
        arr = []
        badd = core_model.APCRM1.objects.filter(
            ap=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "description": bad.description,
                "account": str(bad.account.id),
                "customer": str(bad.customer.id),
                "vatable": bad.vatable,
                "wtax": bad.wtax,
                "discount": bad.discount,
                "amount": bad.amount
            })
            id += 1
        return arr

    def get_wtax1(self, obj):
        arr = []
        badd = core_model.APCRM2.objects.filter(
            ap=obj
        )
        id = 1
        for bad in badd:
            arr.append({
                "id": id,
                "code": str(bad.wtax.id),
                "name": str(bad.wtax.id),
                "tax_amt": bad.taxable_amt,
                "wtax_amt": bad.wtax_amt,
            })
            id += 1
        return arr

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # rep['c_wtax'] = rep.get('c_wtax') or 0

        return rep


class RecurringSerializer(serializers.ModelSerializer):
    ar = serializers.SerializerMethodField()
    ap = serializers.SerializerMethodField()
    period = serializers.CharField(source='get_period_display')
    next = serializers.SerializerMethodField()

    class Meta:
        model = core_model.RecTrans
        fields = ['id', 'ar', 'ap', 'name', 'period',
                  'date', 'sdate', 'next', 'valid', 'status']

    def get_ar(self, obj):
        return obj.ar.invoice_num if obj.ar else 0

    def get_ap(self, obj):
        return obj.ap.invoice_num if obj.ap else 0

    def get_next(self, obj):
        trans = core_model.RecDates.objects.filter(
            rt=obj,
            status=1
        ).order_by('id').first()
        if trans:
            return trans.date
        else:
            return ""


class APSerializer(serializers.ModelSerializer):
    date = serializers.CharField(source="posting_date")
    invoice = serializers.CharField(source="invoice_num")
    vendor = serializers.CharField(source="bp_name")

    balance = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = core_model.APOINV
        fields = ['id', 'date', 'due_date', 'invoice', 'vendor',
                  'po_num', 'status', 'balance', 'total']

    def get_balance(self, obj):
        if obj.status > 2:
            return 0
        else:
            return (
                sf.round2(obj.total) -
                sf.round2(obj.applied_amt) -
                sf.round2(obj.applied_tax)
            )

    def get_total(self, obj):
        cm = core_model.APOCRM.objects.filter(
            ap=obj,
            status=3,
        ).aggregate(
            total=Sum('total', output_field=DecimalField())
        )['total'] or 0
        return (
            sf.round2(obj.total) - cm
        )


class RecTransSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.RecDates
        fields = ['id', 'date', 'date_exe', 'status']


class IncomingInvoicesSerializer(serializers.ModelSerializer):
    checkbox = serializers.SerializerMethodField()
    doc_num = serializers.CharField(source="invoice_num")
    type = serializers.SerializerMethodField()
    date = serializers.CharField(source="posting_date")
    overdue = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    wtax = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = core_model.AROINV
        fields = ['id', 'checkbox', 'doc_num', 'type', 'date',
                  'overdue', 'total', 'wtax', 'balance', 'payment']

    def get_checkbox(self, obj):
        return False

    def get_type(self, obj):
        return "A/R"

    def get_overdue(self, obj):
        if not obj.receipt_date:
            return 0

        today = date.today()
        overdue = (today - obj.receipt_date).days

        return max(overdue, 0)

    def get_total(self, obj):
        apl_amt = sf.round2(obj.applied_amt)
        apl_tax = sf.round2(obj.applied_tax)
        # cm = core_model.AROCRM.objects.filter(
        #     ar=obj
        # ).aggregate(
        #     total=Sum('total', output_field=DecimalField())
        # )['total'] or 0
        return obj.total - apl_amt - apl_tax

    def get_wtax(self, obj):
        # cm = core_model.AROCRM.objects.filter(
        #     ar=obj
        # ).aggregate(
        #     total=Sum('wtax', output_field=DecimalField())
        # )['total'] or 0
        return obj.wtax - sf.round2(obj.applied_tax)

    def get_balance(self, obj):
        app = sf.round2(obj.applied_amt)
        tax = sf.round2(obj.applied_tax)
        return (obj.total - app - tax) - (obj.wtax - tax)

    def get_payment(self, obj):
        return "0"


class OutgoingInvoicesSerializer(serializers.ModelSerializer):
    checkbox = serializers.SerializerMethodField()
    doc_num = serializers.CharField(source="invoice_num")
    type = serializers.SerializerMethodField()
    date = serializers.CharField(source="posting_date")
    overdue = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    wtax = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = core_model.APOINV
        fields = ['id', 'checkbox', 'doc_num', 'type', 'date',
                  'overdue', 'total', 'wtax', 'balance', 'payment']

    def get_checkbox(self, obj):
        return False

    def get_type(self, obj):
        return "A/P"

    def get_overdue(self, obj):
        if not obj.due_date:
            return 0

        today = date.today()
        overdue = (today - obj.due_date).days

        return max(overdue, 0)

    def get_total(self, obj):
        apl_amt = sf.round2(obj.applied_amt)
        apl_tax = sf.round2(obj.applied_tax)
        return obj.total - apl_amt - apl_tax

    def get_wtax(self, obj):
        return obj.wtax - sf.round2(obj.applied_tax)

    def get_balance(self, obj):
        app = sf.round2(obj.applied_amt)
        tax = sf.round2(obj.applied_tax)
        return (obj.total - (app + tax)) - (obj.wtax - tax)

    def get_payment(self, obj):
        return "0"


class IncomingTransactionsSerializer(serializers.ModelSerializer):
    invoices = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display")

    class Meta:
        model = core_model.INCPAY
        fields = ['id', 'doc_no', 'posting_date', 'bp_name',
                  'invoices', 'status', 'total_amt', 'type',
                  'type_display']

    def get_invoices(self, obj):
        return list(
            core_model.INCPAY1.objects
            .filter(inc=obj)
            .values_list("invoice__invoice_num", flat=True)
        )


class OutgoingTransactionsSerializer(serializers.ModelSerializer):
    invoices = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display")

    class Meta:
        model = core_model.OUTPAY
        fields = ['id', 'doc_no', 'posting_date', 'bp_name',
                  'invoices', 'status', 'total_amt', 'type',
                  'type_display']

    def get_invoices(self, obj):
        return list(
            core_model.OUTPAY1.objects
            .filter(out=obj)
            .values_list("invoice__invoice_num", flat=True)
        )


class IncSerializer(serializers.ModelSerializer):
    bpid = serializers.IntegerField(source="code.id")
    bpcode = serializers.CharField(source="bp_code")
    bpname = serializers.CharField(source="bp_name")
    invoice = serializers.CharField(source="doc_no")
    or_num = serializers.CharField()
    post_date = serializers.CharField(source="posting_date")
    poa = serializers.CharField(source="payment_account")
    total_due = serializers.CharField(source="total_amt")
    paid = serializers.CharField(source="total_amt")
    p_type = serializers.SerializerMethodField()
    bank_id = serializers.SerializerMethodField()
    bank_code = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    check_no = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    transfer_date = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()
    cancel = serializers.SerializerMethodField()

    class Meta:
        model = core_model.INCPAY
        fields = [
            'id',
            'bpid',
            'bpcode',
            'bpname',
            'or_num',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'remarks',
            'poa',
            'total_due',
            'paid',
            'p_type',
            'bank_id',
            'bank_code',
            'bank_name',
            'check_no',
            'reference',
            'transfer_date',
            'invoices',
            'status',
            'cancel'
        ]

    def _get_incpay2(self, obj):
        if not hasattr(obj, "_incpay2_cache"):
            obj._incpay2_cache = (
                core_model.INCPAY2.objects
                .filter(inc=obj)
                .first()
            )
        return obj._incpay2_cache

    def get_p_type(self, obj):
        que = self._get_incpay2(obj)
        return str(que.type) if que else None

    def get_bank_id(self, obj):
        que = self._get_incpay2(obj)
        return que.account.id if que else None

    def get_bank_code(self, obj):
        que = self._get_incpay2(obj)
        return que.account.code if que else None

    def get_bank_name(self, obj):
        que = self._get_incpay2(obj)
        return que.account.name if que else None

    def get_check_no(self, obj):
        que = self._get_incpay2(obj)
        return que.check_no if que else None

    def get_reference(self, obj):
        que = self._get_incpay2(obj)
        return que.reference if que else None

    def get_transfer_date(self, obj):
        que = self._get_incpay2(obj)
        return que.transfer_date if que else None

    def get_invoices(self, obj):
        inc1 = core_model.INCPAY1.objects.filter(
            inc=obj
        )
        arr = []
        if inc1:
            for inc in inc1:
                print(f"INC here: {inc.id}")
                overdue = 0
                if not inc.invoice.receipt_date:
                    overdue = 0
                else:
                    today = obj.posting_date
                    overdue = (today - inc.invoice.receipt_date).days
                    overdue = max(overdue, 0)

                arr.append({
                    "id": inc.id,
                    "checkbox": True,
                    "doc_num": inc.invoice.invoice_num,
                    "type": "A/R",
                    "date": inc.invoice.posting_date,
                    "overdue": overdue,
                    "total": inc.amount,
                    "wtax": inc.wtax,
                    "balance": inc.amount,
                    "payment": inc.pay_bal
                })
        return arr

    def get_cancel(self, obj):
        que = core_model.OJDT.objects.filter(
            origin=6,
            origin_no=str(obj.id),
            remarks__icontains="ancellation"
        ).first()
        return que.id if que else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["or"] = data.pop("or_num")
        return data


class OutSerializer(serializers.ModelSerializer):
    bpid = serializers.IntegerField(source="code.id")
    bpcode = serializers.CharField(source="bp_code")
    bpname = serializers.CharField(source="bp_name")
    invoice = serializers.CharField(source="doc_no")
    or_num = serializers.CharField()
    post_date = serializers.CharField(source="posting_date")
    poa = serializers.CharField(source="payment_account")
    total_due = serializers.CharField(source="total_amt")
    paid = serializers.CharField(source="total_amt")
    p_type = serializers.SerializerMethodField()
    bank_id = serializers.SerializerMethodField()
    bank_code = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    check_no = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    transfer_date = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()

    class Meta:
        model = core_model.OUTPAY
        fields = [
            'id',
            'bpid',
            'bpcode',
            'bpname',
            'or_num',
            'invoice',
            'post_date',
            'due_date',
            'doc_date',
            'remarks',
            'poa',
            'total_due',
            'paid',
            'p_type',
            'bank_id',
            'bank_code',
            'bank_name',
            'check_no',
            'reference',
            'transfer_date',
            'invoices',
            'status'
        ]

    def _get_incpay2(self, obj):
        if not hasattr(obj, "_incpay2_cache"):
            obj._incpay2_cache = (
                core_model.OUTPAY2.objects
                .filter(out=obj)
                .first()
            )
        return obj._incpay2_cache

    def get_p_type(self, obj):
        que = self._get_incpay2(obj)
        return str(que.type) if que else None

    def get_bank_id(self, obj):
        que = self._get_incpay2(obj)
        return que.account.id if que else None

    def get_bank_code(self, obj):
        que = self._get_incpay2(obj)
        return que.account.code if que else None

    def get_bank_name(self, obj):
        que = self._get_incpay2(obj)
        return que.account.name if que else None

    def get_check_no(self, obj):
        que = self._get_incpay2(obj)
        return que.check_no if que else None

    def get_reference(self, obj):
        que = self._get_incpay2(obj)
        return que.reference if que else None

    def get_transfer_date(self, obj):
        que = self._get_incpay2(obj)
        return que.transfer_date if que else None

    def get_invoices(self, obj):
        inc1 = core_model.OUTPAY1.objects.filter(
            out=obj
        )
        arr = []
        if inc1:
            for inc in inc1:
                print(f"INC here: {inc.id}")
                arr.append({
                    "id": inc.id,
                    "checkbox": True,
                    "doc_num": inc.invoice.invoice_num,
                    "type": "A/P",
                    "date": inc.invoice.posting_date,
                    "overdue": 0,
                    "total": inc.amount,
                    "wtax": inc.wtax,
                    "balance": inc.amount,
                    "payment": inc.pay_bal
                })
        return arr

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["or"] = data.pop("or_num")
        return data


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Accounts
        fields = ['id', 'name', 'check_no', 'status']


class JETransactionsSerializer(serializers.Serializer):
    # origin = serializers.CharField(source="get_origin_display")
    # date = serializers.CharField(source="post_date")
    # amount = serializers.CharField(source="total")

    # class Meta:
    #     model = core_model.OJDT
    #     fields = ['id', 'no', 'origin', 'date',
    #               'remarks', 'amount']
    id = serializers.IntegerField()
    no = serializers.CharField()
    origin = serializers.CharField()
    date = serializers.DateField()
    remarks = serializers.CharField()
    amount = serializers.DecimalField(max_digits=19, decimal_places=4)
    ref = serializers.IntegerField()


class JETempTransactionsSerializer(serializers.ModelSerializer):
    origin = serializers.CharField(source="get_origin_display")
    date = serializers.CharField(source="post_date")
    amount = serializers.CharField(source="total")

    class Meta:
        model = core_model.OJDTTemp
        fields = ['id', 'no', 'origin', 'date',
                  'remarks', 'amount', 'status']


class JETransactionPreviewSerializer(serializers.ModelSerializer):
    rows = serializers.SerializerMethodField()
    origin = serializers.CharField(source="get_origin_display")

    class Meta:
        model = core_model.OJDT
        fields = ['id', 'no', 'origin', 'origin_no',
                  'remarks', 'post_date', 'due_date',
                  'doc_date', 'trans_no', 'total', 'rows']

    def get_rows(self, obj):
        jdt1 = core_model.JDT1.objects.filter(
            je=obj
        )
        arr = []
        if jdt1:
            for jdt in jdt1:
                arr.append({
                    "id": jdt.id,
                    "code": str(jdt.account.id),
                    "name": jdt.name,
                    "debit": jdt.debit,
                    "credit": jdt.credit,
                    "customer": jdt.bp.id if jdt.bp else 0,
                    "remarks": jdt.remarks,
                })
        return arr


class JETempTransactionPreviewSerializer(serializers.ModelSerializer):
    rows = serializers.SerializerMethodField()
    origin = serializers.CharField(source="get_origin_display")

    class Meta:
        model = core_model.OJDTTemp
        fields = ['id', 'no', 'origin', 'origin_no',
                  'remarks', 'post_date', 'due_date',
                  'doc_date', 'trans_no', 'total', 'rows', 'status']

    def get_rows(self, obj):
        jdt1 = core_model.JDT1Temp.objects.filter(
            je=obj
        )
        arr = []
        if jdt1:
            for jdt in jdt1:
                arr.append({
                    "id": jdt.id,
                    "code": str(jdt.account.id),
                    "name": jdt.name,
                    "debit": jdt.debit,
                    "credit": jdt.credit,
                    "customer": jdt.bp.id if jdt.bp else 0,
                    "remarks": jdt.remarks,
                })
        return arr


class BankStatementSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = core_model.BankRecon
        fields = ['id', 'date', 'description', 'check_no',
                  'status', 'amount', 'date_recon', 'invoices']

    def get_amount(self, obj):
        return obj.debit - obj.credit


class InventorySerializer(serializers.ModelSerializer):
    p_cost = serializers.CharField(source="cost")
    p_sales = serializers.CharField(source="sales")
    p_cogs = serializers.CharField(source="cogs.id")
    p_income = serializers.CharField(source="income.id")

    class Meta:
        model = core_model.Inventory
        fields = ['id', 'code', 'name', 'vendor',
                  'p_cost', 'p_sales', 'stock',
                  'p_cogs', 'p_income', 'uom', 'status']


class ARTermsSerializer(serializers.ModelSerializer):
    bank = serializers.CharField(source="bank_name")
    name = serializers.CharField(source="acc_name")
    no = serializers.CharField(source="acc_no")
    code = serializers.CharField(source="swift_code")

    class Meta:
        model = core_model.PaymentTermsAR
        fields = ['id', 'bank', 'name', 'no', 'code']


class ClientAllSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="client_name")

    class Meta:
        model = core_model.Client
        fields = [
            'id', 'name', 'alias', 'description', 'c_name',
            'c_no', 'address', 'address1', 'tin', 'email',
            'logo', 'license', 'status'
        ]


class ModulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Modules
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Roles
        fields = '__all__'


class AccessAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = core_model.Access
        fields = [
            'module',
            'view',
            'create',
            'edit',
            'delete'
        ]
