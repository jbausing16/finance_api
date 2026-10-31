from collections import defaultdict
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from core import models as core_models
from core.core_functions import Core


class Command(BaseCommand):
    help = "Reset only A/R data inserted via Bulk Import (client id=1)."

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            client = core_models.Client.objects.filter(id=1).first()
            if not client:
                self.stdout.write(self.style.WARNING("Client id=1 not found. Nothing to reset."))
                return

            bulk_invoice_qs = core_models.AROINV.objects.filter(
                client=client,
                source_type="Bulk Import",
            )
            bulk_invoice_ids = list(bulk_invoice_qs.values_list("id", flat=True))

            if not bulk_invoice_ids:
                self.stdout.write(self.style.WARNING("No bulk-imported A/R invoices found. Nothing to reset."))
                return

            linked_cm_qs = core_models.AROCRM.objects.filter(
                client=client,
                ar_id__in=bulk_invoice_ids,
            )
            linked_cm_ids = list(linked_cm_qs.values_list("id", flat=True))

            products_updated = self._reverse_inventory_stock(
                client=client,
                bulk_invoice_ids=bulk_invoice_ids,
                linked_cm_ids=linked_cm_ids,
            )

            bulk_invoice_ids_str = [str(inv_id) for inv_id in bulk_invoice_ids]
            linked_cm_ids_str = [str(cm_id) for cm_id in linked_cm_ids]

            ojdt_filter = Q(origin=2, trans_no__in=bulk_invoice_ids_str)
            if linked_cm_ids_str:
                ojdt_filter |= Q(origin=3, trans_no__in=linked_cm_ids_str)

            bulk_ojdt_qs = core_models.OJDT.objects.filter(client=client).filter(ojdt_filter)
            bulk_ojdt_count = bulk_ojdt_qs.count()
            bulk_ojdt_qs.delete()

            linked_cm_count = linked_cm_qs.count()
            linked_cm_qs.delete()

            bulk_invoice_count = bulk_invoice_qs.count()
            bulk_invoice_qs.delete()

            accounts_rebuilt = self._rebuild_account_balances(client)

            self.stdout.write(self.style.SUCCESS("Bulk reset completed."))
            self.stdout.write(
                (
                    f"Deleted bulk invoices: {bulk_invoice_count} | "
                    f"Deleted linked credit memos: {linked_cm_count} | "
                    f"Deleted linked journals: {bulk_ojdt_count}"
                )
            )
            self.stdout.write(
                (
                    f"Adjusted inventory products: {products_updated} | "
                    f"Rebuilt account balances for: {accounts_rebuilt} account(s)"
                )
            )

    def _reverse_inventory_stock(self, client, bulk_invoice_ids, linked_cm_ids):
        stock_deltas = defaultdict(int)

        invoice_qty_rows = core_models.ARINV1.objects.filter(
            ar_id__in=bulk_invoice_ids,
            product_id__isnull=False,
        ).values("product_id").annotate(
            total_qty=Coalesce(
                Sum("qty"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )

        for row in invoice_qty_rows:
            stock_deltas[row["product_id"]] += Core.round0(row["total_qty"])

        if linked_cm_ids:
            cm_qty_rows = core_models.ARCRM1.objects.filter(
                ar_id__in=linked_cm_ids,
                product_id__isnull=False,
            ).values("product_id").annotate(
                total_qty=Coalesce(
                    Sum("qty"),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )

            for row in cm_qty_rows:
                stock_deltas[row["product_id"]] -= Core.round0(row["total_qty"])

        updated_count = 0
        for product_id, delta in stock_deltas.items():
            if delta == 0:
                continue

            product = core_models.Inventory.objects.filter(
                id=product_id,
                client=client,
            ).first()
            if not product:
                continue

            product.stock = (product.stock or 0) + delta
            product.save(update_fields=["stock"])
            updated_count += 1

        return updated_count

    def _rebuild_account_balances(self, client):
        core_models.Accounts.objects.filter(client=client).update(balance=Decimal("0.00"))

        totals = core_models.JDT1.objects.filter(
            je__client=client,
            account_id__isnull=False,
        ).values("account_id").annotate(
            balance=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("debit") - F("credit"),
                        output_field=DecimalField(max_digits=20, decimal_places=2),
                    )
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )

        updated_count = 0
        for row in totals:
            balance = Core.round2(row["balance"] or Decimal("0.00"))
            core_models.Accounts.objects.filter(
                client=client,
                id=row["account_id"],
            ).update(balance=balance)
            updated_count += 1

        return updated_count
