import csv
import os
import re
import uuid
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core import models as core_models
from core.core_functions import Core


class Command(BaseCommand):
    help = "Import historical A/R Invoice records from CSV or XLSX."

    MAX_FILE_SIZE = 10 * 1024 * 1024
    DEFAULT_MAX_ROWS = 2000

    BASE_REQUIRED_FIELDS = {
        "external_ref",
        "posting_date",
        "line_no",
        "amount",
        "vatable",
        "wtax_applicable",
    }
    SERVICE_REQUIRED_FIELDS = {"line_description", "account_code"}
    ITEM_REQUIRED_FIELDS = {"item_code", "qty", "price"}

    INVOICE_LEVEL_FIELDS = [
        "posting_date",
        "due_date",
        "doc_date",
        "receipt_date",
        "po_num",
        "remarks",
        "invoice_num",
        "already_approved",
        "wtax_ids",
        "wtax_taxable_overrides",
        "wtax_amount_overrides",
    ]

    HEADER_ALIASES = {
        "bp_code": "customer_code",
        "line_description": "line_description",
        "description": "line_description",
        "account": "account_code",
        "product_code": "item_code",
        "product": "item_code",
        "line_customer": "line_customer_code",
        "line_customer_bp_code": "line_customer_code",
        "wtax_id": "wtax_ids",
        "is_approved": "already_approved",
        "approved_status": "already_approved",
    }

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to CSV or XLSX file")
        parser.add_argument("--client-id", type=int)
        parser.add_argument("--actor-useracc-id", type=int)
        parser.add_argument(
            "--user",
            "--user-email",
            dest="user_email",
            help="Resolve actor by user email (optionally scoped by --client-id).",
        )
        parser.add_argument(
            "--customer-code",
            required=True,
            help="Header customer code applied to all invoices in this import run.",
        )
        parser.add_argument(
            "--doc-type",
            required=True,
            type=int,
            choices=[1, 2],
            help="1=Item, 2=Service",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--max-rows", type=int, default=self.DEFAULT_MAX_ROWS)
        parser.add_argument("--batch-id", help="Optional import batch UUID")
        parser.add_argument(
            "--invoice-mode",
            choices=["file", "auto"],
            default="file",
            help="Use invoice number from file or auto sequence",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        default_doc_type = options["doc_type"]
        header_customer_code = self._clean(options.get("customer_code"))
        max_rows = options["max_rows"]
        dry_run = options["dry_run"]
        invoice_mode = options["invoice_mode"]

        if max_rows < 1:
            raise CommandError("--max-rows must be >= 1")

        client, actor = self._resolve_client_and_actor(options)
        header_customer_obj = self._resolve_header_customer(client, header_customer_code)

        batch_id = options.get("batch_id")
        if batch_id:
            try:
                batch_id = uuid.UUID(batch_id)
            except ValueError as exc:
                raise CommandError("Invalid --batch-id UUID.") from exc
        else:
            batch_id = uuid.uuid4()

        self._validate_input_file(file_path)
        raw_rows = self._load_rows(file_path, max_rows)

        if not raw_rows:
            raise CommandError("No data rows found in import file.")

        errors = []
        parsed_rows = self._parse_rows(
            raw_rows=raw_rows,
            default_doc_type=default_doc_type,
            invoice_mode=invoice_mode,
            errors=errors,
        )

        grouped = self._group_rows(
            parsed_rows=parsed_rows,
            errors=errors,
        )

        contains_item_docs = default_doc_type == 1

        dependencies = self._load_dependencies(
            client=client,
            contains_item_docs=contains_item_docs,
        )

        self._resolve_lookups(
            client=client,
            grouped=grouped,
            header_customer_obj=header_customer_obj,
            errors=errors,
        )

        self._validate_group_dependencies(
            client=client,
            grouped=grouped,
            errors=errors,
        )

        if errors:
            self._raise_validation_errors(errors)

        for group in grouped.values():
            group["computed"] = self._compute_group_values(group)

        self.stdout.write(self.style.SUCCESS("Validation successful."))
        self.stdout.write(
            f"Rows: {len(parsed_rows)} | Invoices: {len(grouped)} | Batch: {batch_id}"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No rows were written."))
            return

        created_ids = self._write_groups(
            client=client,
            actor=actor,
            grouped=grouped,
            file_path=file_path,
            batch_id=batch_id,
            invoice_mode=invoice_mode,
            dependencies=dependencies,
        )

        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(
            f"Imported invoices: {len(created_ids)} | IDs: {created_ids[:20]}"
        )

    def _resolve_client_and_actor(self, options):
        client_id = options.get("client_id")
        actor_useracc_id = options.get("actor_useracc_id")
        user_email = self._clean(options.get("user_email"))

        if user_email:
            actor_qs = core_models.UserAcc.objects.filter(user__email=user_email)
            if actor_useracc_id:
                actor_qs = actor_qs.filter(id=actor_useracc_id)
            if client_id:
                actor_qs = actor_qs.filter(client_id=client_id)

            actors = list(actor_qs.select_related("client")[:2])
            if not actors:
                raise CommandError(
                    "No UserAcc found for provided --user/--user-email (and filters)."
                )
            if len(actors) > 1:
                raise CommandError(
                    "Multiple UserAcc matched this user. Provide --client-id or --actor-useracc-id."
                )

            actor = actors[0]
            if not actor.client_id:
                raise CommandError("Resolved UserAcc has no client.")

            client = actor.client or core_models.Client.objects.filter(id=actor.client_id).first()
            if not client:
                raise CommandError("Client not found for resolved UserAcc.")

            return client, actor

        if not client_id:
            raise CommandError(
                "--client-id is required when --user/--user-email is not provided."
            )
        if not actor_useracc_id:
            raise CommandError(
                "--actor-useracc-id is required when --user/--user-email is not provided."
            )

        client = core_models.Client.objects.filter(id=client_id).first()
        if not client:
            raise CommandError("Client not found.")

        actor = core_models.UserAcc.objects.filter(id=actor_useracc_id).first()
        if not actor:
            raise CommandError("Actor UserAcc not found.")

        if actor.client_id != client.id:
            raise CommandError("Actor UserAcc does not belong to provided client.")

        return client, actor

    def _validate_input_file(self, file_path):
        if not os.path.exists(file_path):
            raise CommandError("Input file not found.")

        if not os.path.isfile(file_path):
            raise CommandError("Input path is not a file.")

        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise CommandError("File exceeds 10MB limit.")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".csv", ".xlsx"]:
            raise CommandError("Only CSV and XLSX files are supported.")

    def _resolve_header_customer(self, client, customer_code):
        if not customer_code:
            raise CommandError("--customer-code is required.")

        matches = list(
            core_models.BusinessPartner.objects.filter(
                client=client,
                type=1,
                code=customer_code,
            ).order_by("id")[:2]
        )

        if not matches:
            raise CommandError(f"Unknown --customer-code for client: {customer_code}")

        if len(matches) > 1:
            raise CommandError(
                f"Non-unique --customer-code for client: {customer_code}"
            )

        return matches[0]

    def _load_rows(self, file_path, max_rows):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return self._load_csv_rows(file_path, max_rows)

        return self._load_xlsx_rows(file_path, max_rows)

    def _load_csv_rows(self, file_path, max_rows):
        rows = []
        with open(file_path, "r", encoding="utf-8-sig", newline="") as file_obj:
            reader = csv.reader(file_obj)
            header = next(reader, None)
            if not header:
                return []

            norm_headers = [self._normalize_header(col) for col in header]
            norm_headers = [self.HEADER_ALIASES.get(col, col) for col in norm_headers]

            for row_num, row in enumerate(reader, start=2):
                if self._is_blank_row(row):
                    continue

                if len(rows) >= max_rows:
                    raise CommandError(f"Row limit exceeded ({max_rows}).")

                row_data = {
                    norm_headers[idx]: row[idx] if idx < len(row) else ""
                    for idx in range(len(norm_headers))
                }
                row_data["__row_num"] = row_num
                rows.append(row_data)

        return rows

    def _load_xlsx_rows(self, file_path, max_rows):
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise CommandError("openpyxl is required for XLSX import.") from exc

        rows = []
        workbook = load_workbook(file_path, data_only=True, read_only=True)
        worksheet = workbook.active

        iter_rows = worksheet.iter_rows(values_only=True)
        header = next(iter_rows, None)
        if not header:
            return []

        norm_headers = [self._normalize_header(col) for col in header]
        norm_headers = [self.HEADER_ALIASES.get(col, col) for col in norm_headers]

        for row_num, row in enumerate(iter_rows, start=2):
            if self._is_blank_row(row):
                continue

            if len(rows) >= max_rows:
                raise CommandError(f"Row limit exceeded ({max_rows}).")

            row_data = {
                norm_headers[idx]: row[idx] if idx < len(row) else ""
                for idx in range(len(norm_headers))
            }
            row_data["__row_num"] = row_num
            rows.append(row_data)

        return rows

    def _load_dependencies(self, client, contains_item_docs):
        dependencies = {
            "doc_no_ar": core_models.DocumentNo.objects.filter(
                client=client,
                name="A/R Invoice",
            ).first(),
            "doc_no_je": core_models.DocumentNo.objects.filter(
                client=client,
                name="Journal Entry",
            ).first(),
            "approver": core_models.Approval.objects.filter(
                client=client,
                module="A/R Invoice Approver",
            ).first(),
            "verifier": core_models.Approval.objects.filter(
                client=client,
                module="A/R Invoice Verifier",
            ).first(),
            "ae_ar": core_models.AutoEntries.objects.filter(
                client=client,
                type="A/R Account",
            ).first(),
            "ae_vat": core_models.AutoEntries.objects.filter(
                client=client,
                type="Output VAT",
            ).first(),
            "ae_inventory": core_models.AutoEntries.objects.filter(
                client=client,
                type="Inventory Account",
            ).first(),
        }

        missing = []
        if not dependencies["doc_no_ar"]:
            missing.append("DocumentNo: A/R Invoice")
        if not dependencies["doc_no_je"]:
            missing.append("DocumentNo: Journal Entry")
        if not dependencies["ae_ar"] or not dependencies["ae_ar"].account:
            missing.append("AutoEntries: A/R Account with linked account")
        if not dependencies["ae_vat"] or not dependencies["ae_vat"].account:
            missing.append("AutoEntries: Output VAT with linked account")
        if contains_item_docs and (
            not dependencies["ae_inventory"] or not dependencies["ae_inventory"].account
        ):
            missing.append("AutoEntries: Inventory Account with linked account")

        if missing:
            raise CommandError(
                "Missing setup dependencies:\n- " + "\n- ".join(missing)
            )

        return dependencies

    def _parse_rows(self, raw_rows, default_doc_type, invoice_mode, errors):
        self._validate_headers(raw_rows, default_doc_type)

        parsed_rows = []

        for raw in raw_rows:
            row_num = raw["__row_num"]
            parsed = {"__row_num": row_num}

            external_ref = self._clean(raw.get("external_ref"))
            if not external_ref:
                errors.append(self._err(row_num, "external_ref", "Required."))
                continue

            customer_code = self._clean(raw.get("customer_code") or raw.get("bp_code"))
            if not customer_code:
                errors.append(self._err(row_num, "customer_code", "Required."))
                continue

            line_no = self._parse_int(raw.get("line_no"), row_num, "line_no", errors)
            posting_date = self._parse_date(
                raw.get("posting_date"),
                row_num,
                "posting_date",
                errors,
                required=True,
            )

            due_date = self._parse_date(raw.get("due_date"), row_num, "due_date", errors)
            doc_date = self._parse_date(raw.get("doc_date"), row_num, "doc_date", errors)
            receipt_date = self._parse_date(
                raw.get("receipt_date"),
                row_num,
                "receipt_date",
                errors,
            )

            amount = self._parse_decimal(
                raw.get("amount"), row_num, "amount", errors, required=True
            )
            discount = self._parse_decimal(raw.get("discount"), row_num, "discount", errors)
            if discount is None:
                discount = Decimal("0.00")

            vatable = self._parse_yes_no(
                raw.get("vatable"), row_num, "vatable", errors, required=True
            )
            wtax_applicable = self._parse_yes_no(
                raw.get("wtax_applicable"),
                row_num,
                "wtax_applicable",
                errors,
                required=True,
            )
            already_approved = self._parse_already_approved(
                raw.get("already_approved"),
                row_num,
                errors,
            )
            if already_approved is None:
                already_approved = 2

            invoice_num = self._clean(raw.get("invoice_num"))
            po_num = self._clean(raw.get("po_num"))
            remarks = self._clean(raw.get("remarks"))

            wtax_ids = self._clean(raw.get("wtax_ids"))
            wtax_taxable_overrides = self._clean(raw.get("wtax_taxable_overrides"))
            wtax_amount_overrides = self._clean(raw.get("wtax_amount_overrides"))

            row_doc_type = default_doc_type
            row_doc_type_raw = self._clean(raw.get("doc_type"))
            if row_doc_type_raw:
                parsed_doc_type = self._parse_int(
                    row_doc_type_raw,
                    row_num,
                    "doc_type",
                    errors,
                )
                if parsed_doc_type and parsed_doc_type != row_doc_type:
                    errors.append(
                        self._err(
                            row_num,
                            "doc_type",
                            "Row doc_type does not match --doc-type.",
                        )
                    )
                    continue

            if amount is not None and amount <= 0:
                errors.append(self._err(row_num, "amount", "Must be greater than zero."))

            service_description = self._clean(
                raw.get("line_description") or raw.get("description")
            )
            account_code = self._clean(raw.get("account_code") or raw.get("account"))
            item_code = self._clean(raw.get("item_code") or raw.get("product_code") or raw.get("product"))
            qty = self._parse_decimal(raw.get("qty"), row_num, "qty", errors)
            price = self._parse_decimal(raw.get("price"), row_num, "price", errors)

            if row_doc_type == 2:
                if not service_description:
                    errors.append(self._err(row_num, "line_description", "Required for service import."))
                if not account_code:
                    errors.append(self._err(row_num, "account_code", "Required for service import."))
            else:
                if not item_code:
                    errors.append(self._err(row_num, "item_code", "Required for item import."))
                if qty is None:
                    errors.append(self._err(row_num, "qty", "Required for item import."))
                if price is None:
                    errors.append(self._err(row_num, "price", "Required for item import."))
                if qty is not None and qty <= 0:
                    errors.append(self._err(row_num, "qty", "Must be greater than zero."))
                if price is not None and price <= 0:
                    errors.append(self._err(row_num, "price", "Must be greater than zero."))
                if qty is not None and qty != qty.to_integral_value():
                    errors.append(self._err(row_num, "qty", "Fractional quantity is not allowed."))

            if invoice_mode == "auto":
                invoice_num = ""

            parsed.update(
                {
                    "external_ref": external_ref,
                    "doc_type": row_doc_type,
                    "customer_code": customer_code,
                    "posting_date": posting_date,
                    "due_date": due_date,
                    "doc_date": doc_date,
                    "receipt_date": receipt_date,
                    "line_no": line_no,
                    "amount": Core.round2(amount) if amount is not None else None,
                    "discount": Core.round2(discount),
                    "vatable": vatable,
                    "wtax_applicable": wtax_applicable,
                    "invoice_num": invoice_num,
                    "already_approved": already_approved,
                    "po_num": po_num,
                    "remarks": remarks,
                    "line_description": service_description,
                    "account_code": account_code,
                    "item_code": item_code,
                    "qty": Core.round2(qty) if qty is not None else None,
                    "price": Core.round2(price) if price is not None else None,
                    "wtax_ids": wtax_ids,
                    "wtax_taxable_overrides": wtax_taxable_overrides,
                    "wtax_amount_overrides": wtax_amount_overrides,
                }
            )

            parsed_rows.append(parsed)

        return parsed_rows

    def _validate_headers(self, raw_rows, default_doc_type):
        header_set = set(raw_rows[0].keys())
        header_set.discard("__row_num")

        missing = set()
        for field in self.BASE_REQUIRED_FIELDS:
            if field not in header_set:
                missing.add(field)

        if "customer_code" not in header_set and "bp_code" not in header_set:
            missing.add("customer_code")

        if default_doc_type == 2:
            for field in self.SERVICE_REQUIRED_FIELDS:
                if field not in header_set and field != "line_description":
                    missing.add(field)
            if (
                "line_description" not in header_set
                and "description" not in header_set
            ):
                missing.add("line_description")
        elif default_doc_type == 1:
            for field in self.ITEM_REQUIRED_FIELDS:
                if field not in header_set:
                    missing.add(field)

        if missing:
            missing_cols = ", ".join(sorted(missing))
            raise CommandError(f"Missing required column(s): {missing_cols}")

    def _group_rows(self, parsed_rows, errors):
        grouped = OrderedDict()

        for row in parsed_rows:
            key = row["external_ref"]
            if key not in grouped:
                grouped[key] = {
                    "external_ref": key,
                    "header": row,
                    "lines": [],
                    "line_no_seen": set(),
                }

            group = grouped[key]
            if row["line_no"] in group["line_no_seen"]:
                errors.append(
                    self._err(
                        row["__row_num"],
                        "line_no",
                        "Duplicate line_no within the same external_ref.",
                    )
                )
            else:
                group["line_no_seen"].add(row["line_no"])

            self._validate_group_consistency(
                row=row,
                group=group,
                errors=errors,
            )
            group["lines"].append(row)

        for group in grouped.values():
            self._parse_group_wtax(group, errors)

        return grouped

    def _validate_group_consistency(self, row, group, errors):
        header = group["header"]
        for field in self.INVOICE_LEVEL_FIELDS:
            base_value = header.get(field)
            row_value = row.get(field)
            if base_value != row_value:
                errors.append(
                    self._err(
                        row["__row_num"],
                        field,
                        f"Inconsistent invoice-level value for external_ref {group['external_ref']}.",
                    )
                )

    def _parse_group_wtax(self, group, errors):
        header = group["header"]
        row_num = header["__row_num"]

        id_parts = [
            part.strip()
            for part in header.get("wtax_ids", "").split("|")
            if part and str(part).strip()
        ]

        wtax_ids = []
        seen = set()
        for part in id_parts:
            parsed_id = self._parse_int(part, row_num, "wtax_ids", errors)
            if parsed_id is None:
                continue
            if parsed_id not in seen:
                seen.add(parsed_id)
                wtax_ids.append(parsed_id)

        taxable_overrides = self._parse_decimal_pipe(
            header.get("wtax_taxable_overrides", ""),
            row_num,
            "wtax_taxable_overrides",
            errors,
        )
        amount_overrides = self._parse_decimal_pipe(
            header.get("wtax_amount_overrides", ""),
            row_num,
            "wtax_amount_overrides",
            errors,
        )

        if taxable_overrides and len(taxable_overrides) != len(wtax_ids):
            errors.append(
                self._err(
                    row_num,
                    "wtax_taxable_overrides",
                    "Override count must match number of wtax_ids.",
                )
            )

        if amount_overrides and len(amount_overrides) != len(wtax_ids):
            errors.append(
                self._err(
                    row_num,
                    "wtax_amount_overrides",
                    "Override count must match number of wtax_ids.",
                )
            )

        any_wtax = any(line["wtax_applicable"] == 1 for line in group["lines"])
        if any_wtax and not wtax_ids:
            errors.append(
                self._err(
                    row_num,
                    "wtax_ids",
                    "wtax_ids is required when any line has wtax_applicable=Yes.",
                )
            )

        group["wtax_ids"] = wtax_ids
        group["wtax_taxable_overrides"] = taxable_overrides
        group["wtax_amount_overrides"] = amount_overrides

    def _resolve_lookups(self, client, grouped, header_customer_obj, errors):
        customer_usage = defaultdict(list)
        account_usage = defaultdict(list)
        item_usage = defaultdict(list)

        for group in grouped.values():
            for line in group["lines"]:
                customer_usage[line["customer_code"]].append(line["__row_num"])
                if line["doc_type"] == 2 and line["account_code"]:
                    account_usage[line["account_code"]].append(line["__row_num"])
                if line["doc_type"] == 1 and line["item_code"]:
                    item_usage[line["item_code"]].append(line["__row_num"])

        customer_map = self._resolve_customer_codes(client, customer_usage, errors)
        account_map = self._resolve_account_codes(client, account_usage, errors)
        item_map = self._resolve_item_codes(client, item_usage, errors)
        wtax_map = self._resolve_wtax_ids(client, grouped, errors)

        for group in grouped.values():
            group["customer_obj"] = header_customer_obj
            group["wtax_entries"] = [wtax_map.get(wid) for wid in group["wtax_ids"] if wtax_map.get(wid)]

            for line in group["lines"]:
                line["line_customer_obj"] = customer_map.get(line["customer_code"])
                if line["doc_type"] == 2:
                    line["account_obj"] = account_map.get(line["account_code"])
                else:
                    line["product_obj"] = item_map.get(line["item_code"])

                    prod = line.get("product_obj")
                    if prod and (not prod.income or not prod.cogs):
                        errors.append(
                            self._err(
                                line["__row_num"],
                                "item_code",
                                "Item is missing income or COGS account setup.",
                            )
                        )

    def _resolve_customer_codes(self, client, usage, errors):
        if not usage:
            return {}

        rows = core_models.BusinessPartner.objects.filter(
            client=client,
            type=1,
            code__in=list(usage.keys()),
        ).order_by("id")

        grouped = defaultdict(list)
        for row in rows:
            grouped[(row.code or "").strip()].append(row)

        result = {}
        for code, row_nums in usage.items():
            matches = grouped.get(code, [])
            if not matches:
                for row_num in row_nums:
                    errors.append(self._err(row_num, "customer_code", f"Unknown code: {code}"))
                continue
            if len(matches) > 1:
                for row_num in row_nums:
                    errors.append(
                        self._err(row_num, "customer_code", f"Non-unique code for client: {code}")
                    )
                continue
            result[code] = matches[0]

        return result

    def _resolve_account_codes(self, client, usage, errors):
        if not usage:
            return {}

        rows = core_models.Accounts.objects.filter(
            client=client,
            code__in=list(usage.keys()),
        ).order_by("id")

        grouped = defaultdict(list)
        for row in rows:
            grouped[(row.code or "").strip()].append(row)

        result = {}
        for code, row_nums in usage.items():
            matches = grouped.get(code, [])
            if not matches:
                for row_num in row_nums:
                    errors.append(self._err(row_num, "account_code", f"Unknown code: {code}"))
                continue
            if len(matches) > 1:
                for row_num in row_nums:
                    errors.append(
                        self._err(row_num, "account_code", f"Non-unique code for client: {code}")
                    )
                continue
            result[code] = matches[0]

        return result

    def _resolve_item_codes(self, client, usage, errors):
        if not usage:
            return {}

        rows = core_models.Inventory.objects.filter(
            client=client,
            code__in=list(usage.keys()),
        ).order_by("id")

        grouped = defaultdict(list)
        for row in rows:
            grouped[(row.code or "").strip()].append(row)

        result = {}
        for code, row_nums in usage.items():
            matches = grouped.get(code, [])
            if not matches:
                for row_num in row_nums:
                    errors.append(self._err(row_num, "item_code", f"Unknown code: {code}"))
                continue
            if len(matches) > 1:
                for row_num in row_nums:
                    errors.append(
                        self._err(row_num, "item_code", f"Non-unique code for client: {code}")
                    )
                continue
            result[code] = matches[0]

        return result

    def _resolve_wtax_ids(self, client, grouped, errors):
        all_ids = set()
        for group in grouped.values():
            all_ids.update(group["wtax_ids"])

        if not all_ids:
            return {}

        rows = core_models.AutoEntries.objects.filter(client=client, id__in=list(all_ids))
        result = {row.id: row for row in rows}

        for group in grouped.values():
            for wtax_id in group["wtax_ids"]:
                if wtax_id not in result:
                    errors.append(
                        self._err(
                            group["header"]["__row_num"],
                            "wtax_ids",
                            f"Unknown AutoEntries id: {wtax_id}",
                        )
                    )

        return result

    def _validate_group_dependencies(self, client, grouped, errors):
        external_refs = list(grouped.keys())
        existing = set(
            core_models.AROINV.objects.filter(
                client=client,
                external_ref__in=external_refs,
            ).values_list("external_ref", flat=True)
        )

        for ext_ref in sorted(existing):
            row_num = grouped[ext_ref]["header"]["__row_num"]
            errors.append(
                self._err(
                    row_num,
                    "external_ref",
                    f"Already exists for client: {ext_ref}",
                )
            )

        for group in grouped.values():
            posting_date = group["header"]["posting_date"]
            row_num = group["header"]["__row_num"]

            post = core_models.PostingPeriod.objects.filter(
                client=client,
                is_deleted=False,
                from_date__lte=posting_date,
                to_date__gte=posting_date,
            ).first()

            if not post:
                errors.append(
                    self._err(
                        row_num,
                        "posting_date",
                        "No posting period found for date.",
                    )
                )
                continue

            if post.status == 2:
                errors.append(
                    self._err(
                        row_num,
                        "posting_date",
                        "Posting period is closed.",
                    )
                )

    def _compute_group_values(self, group):
        price_bef_vat = Decimal("0.00")
        discount = Decimal("0.00")
        vat = Decimal("0.00")
        si_sum = Decimal("0.00")
        wtax_taxable_base = Decimal("0.00")

        for line in group["lines"]:
            amount = line["amount"]
            line_discount = line["discount"]

            price_bef_vat += amount
            discount += line_discount

            if line["vatable"] == 1:
                line_vat = amount - (amount / Decimal("1.12"))
            else:
                line_vat = Decimal("0.00")

            vat += line_vat

            if line["vatable"] == 1:
                taxable_base = amount / Decimal("1.12")
            else:
                taxable_base = amount

            si = taxable_base - line_discount
            line["si"] = Core.round2(si)
            si_sum += line["si"]

            if line["wtax_applicable"] == 1:
                wtax_taxable_base += line["si"]

        wtax_entries = []
        total_wtax = Decimal("0.00")

        for idx, ae in enumerate(group["wtax_entries"]):
            rate = Core.round2(ae.rate or 0)

            taxable_override = None
            if group["wtax_taxable_overrides"]:
                taxable_override = group["wtax_taxable_overrides"][idx]

            amount_override = None
            if group["wtax_amount_overrides"]:
                amount_override = group["wtax_amount_overrides"][idx]

            taxable_amt = (
                Core.round2(taxable_override)
                if taxable_override is not None
                else Core.round2(wtax_taxable_base)
            )

            if amount_override is not None:
                wtax_amt = Core.round2(amount_override)
            else:
                wtax_amt = Core.round2(taxable_amt * rate)

            total_wtax += wtax_amt
            wtax_entries.append(
                {
                    "ae": ae,
                    "name": str(ae.id),
                    "rate": rate,
                    "taxable_amt": taxable_amt,
                    "wtax_amt": wtax_amt,
                }
            )

        group["computed_wtax_entries"] = wtax_entries

        total = Core.round2(si_sum + vat)

        return {
            "price_bef_vat": Core.round2(price_bef_vat),
            "discount": Core.round2(discount),
            "vat": Core.round2(vat),
            "wtax": Core.round2(total_wtax),
            "total": total,
        }

    def _write_groups(
        self,
        client,
        actor,
        grouped,
        file_path,
        batch_id,
        invoice_mode,
        dependencies,
    ):
        created_ids = []

        with transaction.atomic():
            doc_no_ar = core_models.DocumentNo.objects.select_for_update().get(
                id=dependencies["doc_no_ar"].id
            )
            doc_no_je = core_models.DocumentNo.objects.select_for_update().get(
                id=dependencies["doc_no_je"].id
            )

            ae_ar = dependencies["ae_ar"]
            ae_vat = dependencies["ae_vat"]
            ae_inventory = dependencies["ae_inventory"]

            for group in grouped.values():
                header = group["header"]
                computed = group["computed"]
                bpartner = group["customer_obj"]
                group_doc_type = header["doc_type"]

                if invoice_mode == "file" and header.get("invoice_num"):
                    invoice_no = header.get("invoice_num")
                else:
                    next_inv = self._next_number(doc_no_ar.no, "A/R Invoice DocumentNo")
                    invoice_no = str(next_inv)
                    doc_no_ar.no = str(next_inv)

                ar = core_models.AROINV(
                    client=client,
                    code=bpartner,
                    bp_code=bpartner.code,
                    bp_name=bpartner.name,
                    type=group_doc_type,
                    invoice_num=invoice_no,
                    external_ref=group["external_ref"],
                    source_type="Bulk Import",
                    import_batch_id=batch_id,
                    imported_file_name=os.path.basename(file_path),
                    posting_date=header.get("posting_date"),
                    due_date=header.get("due_date"),
                    doc_date=header.get("doc_date"),
                    receipt_date=header.get("receipt_date"),
                    po_num=header.get("po_num"),
                    remarks=header.get("remarks"),
                    price_bef_vat=computed["price_bef_vat"],
                    discount=computed["discount"],
                    vat=computed["vat"],
                    wtax=computed["wtax"],
                    total=computed["total"],
                    added=actor,
                )

                # Historical invoice imports are treated as finalized open documents.
                ar.status = 1

                ar.save()
                created_ids.append(ar.id)

                for line in group["lines"]:
                    ar1 = core_models.ARINV1(
                        ar=ar,
                        vatable=line["vatable"],
                        wtax=line["wtax_applicable"],
                        amount=line["amount"],
                        discount=line["discount"],
                    )

                    if line["doc_type"] == 2:
                        ar1.description = line["line_description"]
                        ar1.account = line["account_obj"]
                    else:
                        prod = line["product_obj"]
                        ar1.description = prod.name
                        ar1.account = prod.income
                        ar1.product = prod
                        ar1.qty = line["qty"]
                        ar1.price = line["price"]

                    if line["line_customer_obj"]:
                        ar1.customer = line["line_customer_obj"]

                    ar1.save()

                for entry in group["computed_wtax_entries"]:
                    core_models.ARINV2.objects.create(
                        ar=ar,
                        wtax=entry["ae"],
                        name=entry["name"],
                        rate=entry["rate"],
                        taxable_amt=entry["taxable_amt"],
                        wtax_amt=entry["wtax_amt"],
                    )

                if ar.status == 1:
                    next_je = self._next_number(doc_no_je.no, "Journal Entry DocumentNo")
                    doc_no_je.no = str(next_je)

                    ojdt = core_models.OJDT.objects.create(
                        client=client,
                        no=str(next_je),
                        origin=2,
                        origin_no=str(invoice_no),
                        remarks=f"Based on A/R Invoice {invoice_no}",
                        post_date=header.get("posting_date"),
                        due_date=header.get("due_date"),
                        doc_date=header.get("doc_date"),
                        trans_no=str(ar.id),
                        total=computed["total"],
                    )

                    Core.add_JE(
                        ojdt=ojdt,
                        account=ae_ar.account,
                        debit=computed["total"],
                        credit=Decimal("0.00"),
                        remarks="",
                        post_date=header.get("posting_date"),
                        customer=bpartner.id,
                    )
                    ae_ar.account.balance = Core.round2((ae_ar.account.balance or 0) + computed["total"])
                    ae_ar.account.save()

                    if computed["vat"] > 0:
                        Core.add_JE(
                            ojdt=ojdt,
                            account=ae_vat.account,
                            debit=Decimal("0.00"),
                            credit=computed["vat"],
                            remarks="",
                            post_date=header.get("posting_date"),
                            customer=bpartner.id,
                        )
                        ae_vat.account.balance = Core.round2((ae_vat.account.balance or 0) + computed["vat"])
                        ae_vat.account.save()

                    for line in group["lines"]:
                        customer_id = line["line_customer_obj"].id if line["line_customer_obj"] else ""

                        if line["doc_type"] == 2:
                            account = line["account_obj"]
                            Core.add_JE(
                                ojdt=ojdt,
                                account=account,
                                debit=Decimal("0.00"),
                                credit=line["si"],
                                remarks=line["line_description"],
                                post_date=header.get("posting_date"),
                                customer=customer_id,
                            )
                            account.balance = Core.round2((account.balance or 0) + line["si"])
                            account.save()
                        else:
                            prod = line["product_obj"]
                            inv_account = ae_inventory.account
                            Core.add_JE(
                                ojdt=ojdt,
                                account=prod.income,
                                debit=Decimal("0.00"),
                                credit=line["si"],
                                remarks=prod.name,
                                post_date=header.get("posting_date"),
                                customer=customer_id,
                            )
                            prod.income.balance = Core.round2((prod.income.balance or 0) + line["si"])
                            prod.income.save()

                            amt = Core.round2((prod.cost or 0) * line["qty"])
                            Core.add_JE(
                                ojdt=ojdt,
                                account=prod.cogs,
                                debit=amt,
                                credit=Decimal("0.00"),
                                remarks=prod.name,
                                post_date=header.get("posting_date"),
                                customer=customer_id,
                            )
                            prod.cogs.balance = Core.round2((prod.cogs.balance or 0) + line["si"])
                            prod.cogs.save()

                            Core.add_JE(
                                ojdt=ojdt,
                                account=inv_account,
                                debit=Decimal("0.00"),
                                credit=amt,
                                remarks=prod.name,
                                post_date=header.get("posting_date"),
                                customer=customer_id,
                            )
                            inv_account.balance = Core.round2((inv_account.balance or 0) + line["si"])
                            inv_account.save()

                            prod.stock -= int(line["qty"])
                            prod.save()

            doc_no_ar.save()
            doc_no_je.save()

        return created_ids

    def _normalize_header(self, value):
        if value is None:
            return ""
        value = str(value).strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        return value.strip("_")

    def _is_blank_row(self, row):
        for cell in row:
            if cell is None:
                continue
            if str(cell).strip() != "":
                return False
        return True

    def _clean(self, value):
        if value is None:
            return ""
        return str(value).strip()

    def _parse_int(self, value, row_num, field, errors):
        if value is None or str(value).strip() == "":
            errors.append(self._err(row_num, field, "Required."))
            return None

        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            errors.append(self._err(row_num, field, "Must be an integer."))
            return None

    def _parse_decimal(self, value, row_num, field, errors, required=False):
        if value is None or str(value).strip() == "":
            if required:
                errors.append(self._err(row_num, field, "Required."))
            return None

        try:
            return Decimal(str(value).replace(",", "").strip())
        except (InvalidOperation, ValueError):
            errors.append(self._err(row_num, field, "Must be a decimal number."))
            return None

    def _parse_decimal_pipe(self, value, row_num, field, errors):
        raw = self._clean(value)
        if not raw:
            return []

        parsed = []
        for idx, part in enumerate(raw.split("|"), start=1):
            part = part.strip()
            if not part:
                continue
            dec = self._parse_decimal(part, row_num, f"{field}[{idx}]", errors, required=True)
            if dec is not None:
                parsed.append(Core.round2(dec))

        return parsed

    def _parse_yes_no(self, value, row_num, field, errors, required=False):
        if value is None or str(value).strip() == "":
            if required:
                errors.append(self._err(row_num, field, "Required."))
            return None

        normalized = str(value).strip().lower()
        if normalized in ["1", "yes", "y", "true"]:
            return 1
        if normalized in ["2", "no", "n", "false"]:
            return 2

        errors.append(self._err(row_num, field, "Use 1/2 or Yes/No."))
        return None

    def _parse_already_approved(self, value, row_num, errors):
        if value is None or str(value).strip() == "":
            return None

        normalized = str(value).strip().lower()
        if normalized in ["1", "yes", "y", "true", "approved", "open"]:
            return 1
        if normalized in [
            "2",
            "no",
            "n",
            "false",
            "pending",
            "for_approval",
            "for approval",
            "for-approval",
        ]:
            return 2

        errors.append(
            self._err(
                row_num,
                "already_approved",
                "Use 1/2, Yes/No, or Approved/Pending.",
            )
        )
        return None

    def _parse_date(self, value, row_num, field, errors, required=False):
        if value in [None, ""]:
            if required:
                errors.append(self._err(row_num, field, "Required."))
            return None

        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        raw = str(value).strip()
        if raw == "":
            if required:
                errors.append(self._err(row_num, field, "Required."))
            return None

        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

        errors.append(self._err(row_num, field, "Invalid date format."))
        return None

    def _next_number(self, value, label):
        try:
            return int(str(value)) + 1
        except (TypeError, ValueError) as exc:
            raise CommandError(f"{label} has invalid number value.") from exc

    def _err(self, row_num, field, message):
        return {
            "row": row_num,
            "field": field,
            "message": message,
        }

    def _raise_validation_errors(self, errors, max_errors=30):
        lines = []
        for err in errors[:max_errors]:
            lines.append(f"Row {err['row']} | {err['field']}: {err['message']}")

        if len(errors) > max_errors:
            lines.append(f"... and {len(errors) - max_errors} more error(s).")

        raise CommandError("Validation failed:\n" + "\n".join(lines))
