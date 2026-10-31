"""
Django admin customization.
"""
import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from .models import (
    User, UserAcc, Client, Roles, Region, Province, Municipality, Barangay,
    AccCateg, Accounts, PaymentTermsAR, BusinessPartner, BPAddress,
    BPContract, Approval, AutoEntries, PostingPeriod, AROINV, ARINV1, ARINV2,
    AROCRM, ARCRM1, ARCRM2, APOINV, APINV1, APINV2, APOCRM, APCRM1, APCRM2,
    INCPAY, INCPAY1, INCPAY2, OUTPAY, OUTPAY1, OUTPAY2, Types, DocumentNo,
    OJDT, JDT1, RecTrans, RecDates, BankRecon, Inventory, OJDTTemp, JDT1Temp,
    Notifications, Modules, Access, ChangePass
)


class ExportCsvMixin:

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Dispostion'
        ] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow(
                [getattr(obj, field) for field in field_names]
            )
            print(row)

        return response

    export_as_csv.short_description = "Export Selected"


class ARINV1Inline(admin.TabularInline):
    model = ARINV1
    extra = 1


class ARINV2Inline(admin.TabularInline):
    model = ARINV2
    extra = 1


class ARCRM1Inline(admin.TabularInline):
    model = ARCRM1
    extra = 1


class ARCRM2Inline(admin.TabularInline):
    model = ARCRM2
    extra = 1


class APINV1Inline(admin.TabularInline):
    model = APINV1
    extra = 1


class APINV2Inline(admin.TabularInline):
    model = APINV2
    extra = 1


class APCRM1Inline(admin.TabularInline):
    model = APCRM1
    extra = 1


class APCRM2Inline(admin.TabularInline):
    model = APCRM2
    extra = 1


class INCPAY1Inline(admin.TabularInline):
    model = INCPAY1
    extra = 1


class INCPAY2Inline(admin.TabularInline):
    model = INCPAY2
    extra = 1


class OUTPAY1Inline(admin.TabularInline):
    model = OUTPAY1
    extra = 1


class OUTPAY2Inline(admin.TabularInline):
    model = OUTPAY2
    extra = 1


class JDT1Inline(admin.TabularInline):
    model = JDT1
    extra = 1


class RecDatesInline(admin.TabularInline):
    model = RecDates
    extra = 1


class JDT1TempInline(admin.TabularInline):
    model = JDT1Temp
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    ordering = ['id']
    list_display = ['id', 'first_name', 'last_name', 'email', 'username']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal Info'), {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
            )}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (
            _('Important dates'), {'fields': ('last_login',)},
        ),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'first_name',
                'middle_name',
                'last_name',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )


@admin.register(UserAcc)
class UserAccAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'gender',
        'status'
    ]


@admin.register(Client)
class ClientAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client_name', 'address', 'address1',
                    'email', 'tin', 'created_at']
    actions = ["export_as_csv"]


@admin.register(Roles)
class RolesAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'name', 'status']
    actions = ["export_as_csv"]


@admin.register(Region)
class RegionAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'region_id']
    actions = ["export_as_csv"]


@admin.register(Province)
class ProvinceAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'region']
    actions = ["export_as_csv"]


@admin.register(Municipality)
class MunicipalityAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'province']
    actions = ["export_as_csv"]


@admin.register(Barangay)
class BarangayAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'municipality']
    actions = ["export_as_csv"]


@admin.register(AccCateg)
class AccCategAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'name', 'alias', 'status']
    actions = ["export_as_csv"]


@admin.register(Accounts)
class AccountsAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'code', 'name',
                    'category', 'balance', 'status']
    actions = ["export_as_csv"]


@admin.register(PaymentTermsAR)
class PaymentTermsARAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'bank_name', 'acc_name', 'acc_no']
    actions = ["export_as_csv"]


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'type', 'code', 'name', 'tin', 'status']
    actions = ["export_as_csv"]


@admin.register(BPAddress)
class BPAddressAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'bp', 'street', 'barangay', 'zipcode']
    actions = ["export_as_csv"]


@admin.register(BPContract)
class BPContractAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'bp', 'type', 'start_date', 'end_date']
    actions = ["export_as_csv"]


@admin.register(Approval)
class ApprovalAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'module', 'user', 'status']
    actions = ["export_as_csv"]


@admin.register(AutoEntries)
class AutoEntriesAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'module', 'type', 'account', 'rate']
    actions = ["export_as_csv"]


@admin.register(PostingPeriod)
class PostingPeriodAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'year', 'name',
                    'from_date', 'to_date', 'status', 'is_deleted']
    actions = ["export_as_csv"]


@admin.register(AROINV)
class AROINVAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'invoice_num', 'bp_name', 'posting_date',
        'total', 'remarks', 'status', 'cancelation', 'canceledAR'
    ]
    search_fields = ['invoice_num', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [ARINV1Inline, ARINV2Inline]
    actions = ["export_as_csv"]


@admin.register(AROCRM)
class AROCRMAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'invoice_num', 'bp_name', 'posting_date',
        'total', 'ar', 'status'
    ]
    search_fields = ['invoice_num', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [ARCRM1Inline, ARCRM2Inline]
    actions = ["export_as_csv"]


@admin.register(APOINV)
class APOINVAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'invoice_num', 'bp_name', 'posting_date',
        'total', 'status', 'cancelation', 'canceledAP'
    ]
    search_fields = ['invoice_num', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [APINV1Inline, APINV2Inline]
    actions = ["export_as_csv"]


@admin.register(APOCRM)
class APOCRMAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'invoice_num', 'bp_name', 'posting_date',
        'total', 'ap', 'status'
    ]
    search_fields = ['invoice_num', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [APCRM1Inline, APCRM2Inline]
    actions = ["export_as_csv"]


@admin.register(INCPAY)
class INCPAYAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'doc_no', 'bp_name', 'posting_date',
        'total_amt', 'status'
    ]
    search_fields = ['doc_no', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [INCPAY1Inline, INCPAY2Inline]
    actions = ["export_as_csv"]


@admin.register(OUTPAY)
class OUTPAYAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'doc_no', 'bp_name', 'posting_date',
        'total_amt', 'status', 'reconciled'
    ]
    search_fields = ['doc_no', 'bp_name', 'bp_code']
    list_filter = ['status', 'type', 'posting_date']
    inlines = [OUTPAY1Inline, OUTPAY2Inline]
    actions = ["export_as_csv"]


@admin.register(OJDT)
class OJDTAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'no', 'origin', 'origin_no',
        'remarks', 'post_date', 'due_date', 'doc_date',
        'trans_no', 'total', 'status'
    ]
    search_fields = ['origin']
    list_filter = ['status', 'client', 'origin']
    inlines = [JDT1Inline]
    actions = ["export_as_csv"]


@admin.register(OJDTTemp)
class OJDTTempAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = [
        'id', 'client', 'no', 'origin', 'origin_no',
        'remarks', 'post_date', 'due_date', 'doc_date',
        'trans_no', 'total', 'status'
    ]
    search_fields = ['origin']
    list_filter = ['status', 'client', 'origin']
    inlines = [JDT1TempInline]
    actions = ["export_as_csv"]


@admin.register(Types)
class TypesAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(DocumentNo)
class DocumentNoAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'name', 'no']


@admin.register(RecTrans)
class RecTransAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'type', 'ar', 'ap',
                    'name', 'period', 'date', 'sdate',
                    'valid', 'status', 'created_by']
    inlines = [RecDatesInline]


@admin.register(BankRecon)
class BankReconAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'bank', 'date', 'branch',
                    'description', 'debit', 'credit',
                    'r_balance', 'check_no', 'date_recon',
                    'status', 'added_by']


@admin.register(Inventory)
class InventoryAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'code', 'name',
                    'vendor', 'cost', 'sales',
                    'uom', 'cogs', 'income', 'stock',
                    'status', 'added_by']


@admin.register(Notifications)
class NotificationsAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'client', 'sender', 'receiver',
                    'message', 'module', 'is_read',
                    'date_read', 'date_added']


@admin.register(Modules)
class ModulesAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'module', 'sub_module']


@admin.register(Access)
class AccessAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'role', 'module', 'access', 'view',
                    'create', 'edit', 'delete']


@admin.register(ChangePass)
class ChangePassAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'pin', 'date_added']
