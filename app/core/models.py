from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
import uuid
from decimal import Decimal
# from model_utils import Choices


class UserManager(BaseUserManager):
    """Manager for users."""
    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True)
    session_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Client(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]

    client_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    alias = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    c_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    c_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    address1 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    tin = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    email = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    logo = models.ImageField(
        upload_to="client_logo",
        null=True,
        blank=True,
        default=None
    )
    license = models.IntegerField(
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )

    def __str__(self):
        return "%s" % (self.client_name)


class Roles(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )

    def __str__(self):
        return "%s" % (self.name)


class Types(models.Model):
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return "%s" % (self.name)


class UserAcc(models.Model):
    GENDER = [
        (1, "Male"),
        (2, "Female")
    ]

    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name="user_acc"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    profile = models.ImageField(
        upload_to="user_profile",
        null=True,
        blank=True,
        default=None
    )
    signature = models.ImageField(
        upload_to="user_signature",
        null=True,
        blank=True,
        default=None
    )
    gender = models.IntegerField(
        choices=GENDER,
        default=1
    )
    date_hired = models.DateField(
        blank=True,
        null=True
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    user_type = models.ForeignKey(
        Types,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    job_position = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name="user_acc"
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Region(models.Model):
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    region_id = models.IntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Province(models.Model):
    region = models.ForeignKey(
        "Region",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='region'
    )
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Municipality(models.Model):
    province = models.ForeignKey(
        "Province",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='province'
    )
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Barangay(models.Model):
    municipality = models.ForeignKey(
        "Municipality",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='city'
    )
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class AccCateg(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    alias = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )

    def __str__(self):
        return "%s" % (self.name)


class Accounts(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        AccCateg,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    cash = models.BooleanField(default=False)
    wtax = models.BooleanField(default=False)
    parent = models.IntegerField(
        blank=True,
        null=True
    )
    type = models.IntegerField(
        blank=True,
        null=True
    )
    level = models.IntegerField(
        blank=True,
        null=True
    )
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    check_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return "(%s) %s" % (self.id, self.name)


class PaymentTermsAR(models.Model):
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    bank_name = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    acc_name = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    acc_no = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    swift_code = models.CharField(
        max_length=11,
        null=True,
        blank=True
    )

    def __str__(self):
        return "%s - %s" % (
            self.bank_name,
            self.acc_name
        )


class BusinessPartner(models.Model):
    TYPE = [
        (1, "Customer"),
        (2, "Vendor")
    ]
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]

    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=1
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    tin = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    terms = models.IntegerField(
        blank=True,
        null=True
    )
    wtax = models.ForeignKey(
        "AutoEntries",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    tax_stat = models.IntegerField(
        choices=YESNO,
        blank=True,
        null=True
    )
    p_terms = models.ForeignKey(
        PaymentTermsAR,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )


class BPAddress(models.Model):
    bp = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='bp_address'
    )
    street = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    barangay = models.ForeignKey(
        Barangay,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    zipcode = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    c_person = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    c_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    email = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class BPContract(models.Model):
    TYPE = [
        (1, "Simple Contract"),
        (2, "Fixed Priced")
    ]
    bp = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='bp_contract'
    )
    type = models.IntegerField(
        choices=TYPE,
        default=1
    )
    start_date = models.DateField(
        blank=True,
        null=True
    )
    end_date = models.DateField(
        blank=True,
        null=True
    )
    c_person = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    c_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    email = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class Approval(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    module = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    status = models.IntegerField(
        choices=STATUS,
        default=2
    )


class AutoEntries(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    module = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )


class PostingPeriod(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    year = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    from_date = models.DateField(
        blank=True,
        null=True
    )
    to_date = models.DateField(
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    is_deleted = models.BooleanField(
        default=False
    )


class AROINV(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Partially Paid"),
        (3, "Closed"),
        (4, "Canceled"),
        (5, "For Verification"),
        (6, "For Approval"),
        (7, "Declined")
    ]
    TYPE = [
        (1, "Item"),
        (2, "Service")
    ]
    SOURCE_TYPE = [
        ("Manual", "Manual"),
        ("Bulk Import", "Bulk Import"),
    ]
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    invoice_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    external_ref = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE,
        default="Manual",
    )
    import_batch_id = models.UUIDField(
        blank=True,
        null=True,
        db_index=True,
    )
    imported_file_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    receipt_date = models.DateField(
        blank=True,
        null=True
    )
    po_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    price_bef_vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    applied_tax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    applied_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    cancelation = models.BooleanField(
        default=False
    )
    canceledAR = models.ForeignKey(
        "AROINV",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="aroinv_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="aroinv_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="aroinv_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="aroinv_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def _full_name(self, useracc):
        if not useracc or not useracc.user:
            return ""
        user = useracc.user
        return f"{user.first_name} {user.last_name}".strip()

    @property
    def inv_prep(self):
        return self._full_name(self.added)

    @property
    def inv_ver(self):
        return self._full_name(self.verified)

    @property
    def inv_app(self):
        return self._full_name(self.approved)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["client", "external_ref"],
                condition=(
                    models.Q(external_ref__isnull=False)
                    & ~models.Q(external_ref="")
                ),
                name="uq_aroinv_client_external_ref_present",
            )
        ]


class ARINV1(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ar = models.ForeignKey(
        AROINV,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="invRows"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    vatable = models.IntegerField(
        choices=YESNO,
        default=1
    )
    wtax = models.IntegerField(
        choices=YESNO,
        default=1
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    qty = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        "Inventory",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class ARINV2(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ar = models.ForeignKey(
        AROINV,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="invTax"
    )
    wtax = models.ForeignKey(
        AutoEntries,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    taxable_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    paid = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )


class AROCRM(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Partially Paid"),
        (3, "Closed"),
        (4, "Canceled"),
        (5, "For Verification"),
        (6, "For Approval"),
        (7, "Declined")
    ]
    TYPE = [
        (1, "Item"),
        (2, "Service")
    ]
    ar = models.ForeignKey(
        AROINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name="arcrm"
    )
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    invoice_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    po_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    price_bef_vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    applied_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="arocrm_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="arocrm_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="arocrm_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="arocrm_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class ARCRM1(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ar = models.ForeignKey(
        AROCRM,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="crmRows"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    vatable = models.IntegerField(
        choices=YESNO,
        default=1
    )
    wtax = models.IntegerField(
        choices=YESNO,
        default=1
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    qty = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        "Inventory",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class ARCRM2(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ar = models.ForeignKey(
        AROCRM,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="crmTax"
    )
    wtax = models.ForeignKey(
        AutoEntries,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    taxable_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )


class APOINV(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Partially Paid"),
        (3, "Closed"),
        (4, "Canceled"),
        (5, "For Verification"),
        (6, "For Approval"),
        (7, "Declined")
    ]
    TYPE = [
        (1, "Item"),
        (2, "Service")
    ]
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    invoice_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    po_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    price_bef_vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    applied_tax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    applied_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    cancelation = models.BooleanField(
        default=False
    )
    canceledAP = models.ForeignKey(
        "APOINV",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apoinv_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apoinv_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apoinv_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apoinv_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def _full_name(self, useracc):
        if not useracc or not useracc.user:
            return ""
        user = useracc.user
        return f"{user.first_name} {user.last_name}".strip()

    @property
    def inv_prep(self):
        return self._full_name(self.added)

    @property
    def inv_ver(self):
        return self._full_name(self.verified)

    @property
    def inv_app(self):
        return self._full_name(self.approved)


class APINV1(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ap = models.ForeignKey(
        APOINV,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="invAPRows"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    vatable = models.IntegerField(
        choices=YESNO,
        default=1
    )
    wtax = models.IntegerField(
        choices=YESNO,
        default=1
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    qty = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        "Inventory",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class APINV2(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ap = models.ForeignKey(
        APOINV,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="invAPTax"
    )
    wtax = models.ForeignKey(
        AutoEntries,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    taxable_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    paid = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )


class APOCRM(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Partially Paid"),
        (3, "Closed"),
        (4, "Canceled"),
        (5, "For Verification"),
        (6, "For Approval"),
        (7, "Declined")
    ]
    TYPE = [
        (1, "Item"),
        (2, "Service")
    ]
    ap = models.ForeignKey(
        APOINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    invoice_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    po_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    price_bef_vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    vat = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    applied_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apcrm_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apcrm_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apcrm_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="apcrm_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class APCRM1(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ap = models.ForeignKey(
        APOCRM,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="crmAPRows"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    vatable = models.IntegerField(
        choices=YESNO,
        default=1
    )
    wtax = models.IntegerField(
        choices=YESNO,
        default=1
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    qty = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        "Inventory",
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class APCRM2(models.Model):
    YESNO = [
        (1, "Yes"),
        (2, "No")
    ]
    ap = models.ForeignKey(
        APOCRM,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="crmAPTax"
    )
    wtax = models.ForeignKey(
        AutoEntries,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    taxable_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )


class INCPAY(models.Model):
    STATUS = [
        (1, "Closed"),
        (2, "Canceled"),
        (3, "For Verification"),
        (4, "For Approval"),
        (5, "Declined"),
        (6, "Open")
    ]
    TYPE = [
        (1, "Customer"),
        (2, "Vendor"),
        (3, "Account")
    ]
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    doc_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    or_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    payment_account = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=6
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="inc_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="inc_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="inc_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="inc_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    reconciled = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)


class INCPAY1(models.Model):
    inc = models.ForeignKey(
        INCPAY,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="incInv"
    )
    invoice = models.ForeignKey(
        AROINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    pay_bal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    pay_tax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class INCPAY2(models.Model):
    TYPE = [
        (1, "Check"),
        (2, "Bank Transfer"),
        (3, "Cash")
    ]
    inc = models.ForeignKey(
        INCPAY,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="incBank"
    )
    type = models.IntegerField(
        choices=TYPE,
        default=1
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    check_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    transfer_date = models.DateField(
        blank=True,
        null=True
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class OUTPAY(models.Model):
    STATUS = [
        (1, "Closed"),
        (2, "Canceled"),
        (3, "For Verification"),
        (4, "For Approval"),
        (5, "Declined"),
        (6, "Open")
    ]
    TYPE = [
        (1, "Customer"),
        (2, "Vendor"),
        (3, "Account")
    ]
    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    code = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    bp_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    bp_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    type = models.IntegerField(
        choices=TYPE,
        default=2
    )
    doc_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    posting_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    or_num = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    payment_account = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    total_amt = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=6
    )
    reconciled = models.BooleanField(default=False)
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="out_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="out_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="out_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="out_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class OUTPAY1(models.Model):
    out = models.ForeignKey(
        OUTPAY,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="outInv"
    )
    invoice = models.ForeignKey(
        APOINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    wtax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    pay_bal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    pay_tax = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )


class OUTPAY2(models.Model):
    TYPE = [
        (1, "Check"),
        (2, "Bank Transfer"),
        (3, "Cash")
    ]
    out = models.ForeignKey(
        OUTPAY,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="outBank"
    )
    type = models.IntegerField(
        choices=TYPE,
        default=1
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    check_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    transfer_date = models.DateField(
        blank=True,
        null=True
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class DocumentNo(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class OJDT(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Closed"),
        (3, "Canceled"),
        (4, "For Verification"),
        (5, "For Approval"),
        (6, "Declined")
    ]
    ORIGIN = [
        (1, "Journal Entry"),
        (2, "A/R Invoice"),
        (3, "A/R Credit Memo"),
        (4, "A/P Invoice"),
        (5, "A/P Credit Memo"),
        (6, "Incoming Payment"),
        (7, "Outgoing Payment")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    origin = models.IntegerField(
        choices=ORIGIN,
        default=1,
        blank=True,
        null=True
    )
    origin_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    post_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    trans_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdt_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdt_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdt_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdt_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class JDT1(models.Model):
    je = models.ForeignKey(
        OJDT,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name="jdt1_rows"
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='jdt1',
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    debit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    credit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    bp = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    post_date = models.DateField(
        blank=True,
        null=True
    )


class OJDTTemp(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Closed"),
        (3, "Canceled"),
        (4, "For Verification"),
        (5, "For Approval"),
        (6, "Declined")
    ]
    ORIGIN = [
        (1, "Journal Entry"),
        (2, "A/R Invoice"),
        (3, "A/R Credit Memo"),
        (4, "A/P Invoice"),
        (5, "A/P Credit Memo"),
        (6, "Incoming Payment"),
        (7, "Outgoing Payment")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    origin = models.IntegerField(
        choices=ORIGIN,
        default=1,
        blank=True,
        null=True
    )
    origin_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    post_date = models.DateField(
        blank=True,
        null=True
    )
    due_date = models.DateField(
        blank=True,
        null=True
    )
    doc_date = models.DateField(
        blank=True,
        null=True
    )
    trans_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    added = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdttemp_added"
    )
    verified = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdttemp_verified"
    )
    approved = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdttemp_approved"
    )
    declined = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="ojdttemp_declined"
    )
    date_dec = models.DateTimeField(blank=True, null=True)
    date_ver = models.DateTimeField(blank=True, null=True)
    date_app = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class JDT1Temp(models.Model):
    je = models.ForeignKey(
        OJDTTemp,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name="ojdtTemp1"
    )
    account = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        related_name='jdt1temp',
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    debit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    credit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    bp = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    post_date = models.DateField(
        blank=True,
        null=True
    )


class RecTrans(models.Model):
    TYPE = [
        (1, "A/R"),
        (2, "A/P")
    ]
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    PERIOD = [
        (1, "Monthly"),
        (2, "Quarterly"),
        (3, "Semi-Anually"),
        (4, "Anually")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    type = models.IntegerField(
        choices=TYPE,
        default=1
    )
    ar = models.ForeignKey(
        AROINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    ap = models.ForeignKey(
        APOINV,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    period = models.IntegerField(
        choices=PERIOD,
        blank=True,
        null=True
    )
    date = models.IntegerField(
        blank=True,
        null=True
    )
    sdate = models.DateField(
        blank=True,
        null=True
    )
    valid = models.DateField(
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    created_by = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )


class RecDates(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Closed")
    ]
    rt = models.ForeignKey(
        RecTrans,
        on_delete=models.CASCADE,
        db_index=True,
    )
    date = models.DateField(
        blank=True,
        null=True
    )
    date_exe = models.DateField(
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )


class BankRecon(models.Model):
    STATUS = [
        (1, "Open"),
        (2, "Closed")
    ]
    bank = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    date = models.DateField(
        blank=True,
        null=True
    )
    branch = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    debit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    credit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    r_balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    check_no = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    date_recon = models.DateField(
        blank=True,
        null=True
    )
    invoices = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    uniq = models.TextField(
        blank=True,
        null=True
    )
    added_by = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)


class Inventory(models.Model):
    STATUS = [
        (1, "Active"),
        (2, "Inactive")
    ]
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    vendor = models.ForeignKey(
        BusinessPartner,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    cost = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    sales = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    uom = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    cogs = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="cogs"
    )
    income = models.ForeignKey(
        Accounts,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="income"
    )
    status = models.IntegerField(
        choices=STATUS,
        default=1
    )
    stock = models.IntegerField(
        default=0
    )
    added_by = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)


class Notifications(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True
    )
    sender = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="notif_sender"
    )
    receiver = models.ForeignKey(
        UserAcc,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="notif_receiver"
    )
    message = models.TextField(
        blank=True,
        null=True
    )
    module = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    is_read = models.BooleanField(default=False)
    date_read = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(
        default=1
    )


class Modules(models.Model):
    module = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    sub_module = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


class Access(models.Model):
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="access_role"
    )
    module = models.ForeignKey(
        Modules,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
        related_name="access_module"
    )
    access = models.BooleanField(
        blank=True,
        null=True,
        default=True
    )
    view = models.BooleanField(
        blank=True,
        null=True,
        default=True
    )
    create = models.BooleanField(
        blank=True,
        null=True,
        default=True
    )
    edit = models.BooleanField(
        blank=True,
        null=True,
        default=True
    )
    delete = models.BooleanField(
        blank=True,
        null=True,
        default=True
    )


class ChangePass(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_index=True,
        blank=True,
        null=True,
    )
    pin = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)
