# CSV Template Field Guide

## Purpose
This guide documents each column used by the historical AR CSV templates in this folder:
- Invoice Item
- Invoice Service
- Credit Memo Item
- Credit Memo Service

Use this as a field-by-field reference before running import commands.

## Grouping Rules (Applies to All 4 Templates)
1. `external_ref` groups rows into one document header.
2. Rows with the same `external_ref` must keep all header-level fields consistent.
3. `line_no` must be unique within the same `external_ref` group.
4. For credit memos, `invoice_external_ref` must match an existing invoice `external_ref`.

## Value Formats
- Date accepted formats: `YYYY-MM-DD`, `MM/DD/YYYY`, `YYYY/MM/DD`
- Boolean-like fields (`vatable`, `wtax_applicable`): `1/Yes/Y/True` or `2/No/N/False`
- Decimal fields: numeric values; rounded to 2 decimal places by importer
- Pipe fields: values separated by `|` (example: `8|9`)

## Header Aliases
The importer accepts these aliases and maps them to canonical names:

### Shared Aliases
- `bp_code` -> `customer_code`
- `description` -> `line_description`
- `account` -> `account_code`
- `product_code` -> `item_code`
- `product` -> `item_code`
- `line_customer` -> `line_customer_code`
- `line_customer_bp_code` -> `line_customer_code`
- `wtax_id` -> `wtax_ids`

### Invoice-only Aliases
- `is_approved` -> `already_approved`
- `approved_status` -> `already_approved`

### Credit Memo-only Aliases
- `source_invoice_ref` -> `invoice_external_ref`
- `ar_invoice_external_ref` -> `invoice_external_ref`
- `credit_memo_num` -> `invoice_num`
- `cm_num` -> `invoice_num`

---

## 1) Invoice Service Template
Template file: `invoice-service-template.csv`

Columns:

1. `external_ref`
- Required: Yes
- Meaning: Document grouping key for one invoice header.
- Rule: Must be unique per client (cannot already exist in AROINV).

2. `customer_code`
- Required: Yes
- Meaning: Header customer code for the invoice.
- Rule: Must exist as a unique Customer BusinessPartner for the client.

3. `posting_date`
- Required: Yes
- Meaning: Posting date of invoice.
- Rule: Must fall in an existing, open posting period.

4. `due_date`
- Required: No
- Meaning: Due date.

5. `doc_date`
- Required: No
- Meaning: Document date.

6. `receipt_date`
- Required: No
- Meaning: Receipt date.

7. `invoice_num`
- Required: Depends on mode
- Meaning: Invoice number.
- Rule: Used when `--invoice-mode file`; may be auto-generated when `--invoice-mode auto`.

8. `already_approved`
- Required: No
- Meaning: Approval state at import time.
- Default: `2`
- Accepted values: `1/Yes/Y/True/Approved/Open`, `2/No/N/False/Pending/For Approval`

9. `line_no`
- Required: Yes
- Meaning: Line sequence inside one `external_ref` group.
- Rule: Must be unique within the same group.

10. `line_description`
- Required: Yes for Service
- Meaning: Service line description.

11. `account_code`
- Required: Yes for Service
- Meaning: Revenue/service account code used for the line.
- Rule: Must exist as a unique account code for the client.

12. `amount`
- Required: Yes
- Meaning: Gross line amount.
- Rule: Must be greater than zero.

13. `discount`
- Required: No
- Meaning: Line discount amount.
- Default: `0.00`

14. `vatable`
- Required: Yes
- Meaning: Whether line is VATable.
- Accepted values: `1` (Yes), `2` (No).

15. `wtax_applicable`
- Required: Yes
- Meaning: Whether line contributes to WTax base.
- Accepted values: `1` (Yes), `2` (No).

16. `wtax_ids`
- Required: Conditional
- Meaning: WTax AutoEntries IDs applied at document level.
- Format: Pipe-delimited IDs, example `8|9`.
- Rule: Required if any line in the same group has `wtax_applicable=1`.

17. `wtax_taxable_overrides`
- Required: No
- Meaning: Override taxable base per WTax ID.
- Format: Pipe-delimited decimals.
- Rule: If provided, count must equal count of `wtax_ids`.

18. `wtax_amount_overrides`
- Required: No
- Meaning: Override WTax amount per WTax ID.
- Format: Pipe-delimited decimals.
- Rule: If provided, count must equal count of `wtax_ids`.

19. `po_num`
- Required: No
- Meaning: PO or reference number.

20. `remarks`
- Required: No
- Meaning: Header remarks.

---

## 2) Invoice Item Template
Template file: `invoice-item-template.csv`

Columns are same as Invoice Service, with item-specific line fields:

1. `external_ref` (required)
2. `customer_code` (required)
3. `posting_date` (required)
4. `due_date` (optional)
5. `doc_date` (optional)
6. `receipt_date` (optional)
7. `invoice_num` (mode-dependent)
8. `already_approved` (optional, default `2`)
9. `line_no` (required)
10. `item_code` (required for Item)
- Meaning: Inventory item code.
- Rule: Must exist as a unique Inventory code for the client.
11. `account_code` (optional in Item template)
- Meaning: Not required by Item validation path; template may include it for reference.
12. `qty` (required for Item)
- Rule: Must be greater than zero and integral.
13. `price` (required for Item)
- Rule: Must be greater than zero.
14. `amount` (required)
15. `discount` (optional, default `0.00`)
16. `vatable` (required)
17. `wtax_applicable` (required)
18. `wtax_ids` (conditional)
19. `wtax_taxable_overrides` (optional)
20. `wtax_amount_overrides` (optional)
21. `po_num` (optional)
22. `remarks` (optional)

Important Item rules:
- `item_code` product must have both income and COGS account setup.
- `qty` must be whole-number quantity.

---

## 3) Credit Memo Service Template
Template file: `credit-memo-service-template.csv`

Columns:

1. `external_ref`
- Required: Yes
- Meaning: Group key of one credit memo document.

2. `invoice_external_ref`
- Required: Yes
- Meaning: Source invoice external reference to apply credit memo against.
- Rule: Must exist in AROINV for the same client.

3. `customer_code`
- Required: Yes
- Rule: Must match header customer and linked invoice customer context.

4. `posting_date`
- Required: Yes
- Rule: Must fall in open posting period.

5. `due_date`
- Required: No

6. `doc_date`
- Required: No

7. `invoice_num`
- Required: Depends on mode
- Rule: Required for `--credit-memo-mode file`; auto-generated in `--credit-memo-mode auto`.

8. `line_no`
- Required: Yes
- Rule: Unique within same `external_ref` group.

9. `line_description`
- Required: Yes for Service

10. `account_code`
- Required: Yes for Service
- Rule: Must exist as unique account code for client.

11. `amount`
- Required: Yes
- Rule: Must be greater than zero.

12. `discount`
- Required: No
- Default: `0.00`

13. `vatable`
- Required: Yes

14. `wtax_applicable`
- Required: Yes

15. `wtax_ids`
- Required: Conditional
- Rule: Required only if any line has `wtax_applicable=1`.

16. `wtax_taxable_overrides`
- Required: No
- Rule: Count must match `wtax_ids` when provided.

17. `wtax_amount_overrides`
- Required: No
- Rule: Count must match `wtax_ids` when provided.

18. `po_num`
- Required: No

19. `remarks`
- Required: No

Additional credit memo rule:
- Computed credit memo total must not exceed linked invoice outstanding balance.

---

## 4) Credit Memo Item Template
Template file: `credit-memo-item-template.csv`

Columns are same as Credit Memo Service, with item-specific line fields:

1. `external_ref` (required)
2. `invoice_external_ref` (required)
3. `customer_code` (required)
4. `posting_date` (required)
5. `due_date` (optional)
6. `doc_date` (optional)
7. `invoice_num` (mode-dependent)
8. `line_no` (required)
9. `item_code` (required for Item)
10. `qty` (required for Item, > 0 and integral)
11. `price` (required for Item, > 0)
12. `amount` (required)
13. `discount` (optional, default `0.00`)
14. `vatable` (required)
15. `wtax_applicable` (required)
16. `wtax_ids` (conditional)
17. `wtax_taxable_overrides` (optional)
18. `wtax_amount_overrides` (optional)
19. `po_num` (optional)
20. `remarks` (optional)

Item-specific CM rules:
- `item_code` must resolve to existing Inventory item.
- Item must have income and COGS account setup.

---

## Cross-Template Differences
1. Invoice templates include `receipt_date` and `already_approved`; credit memo templates do not.
2. Credit memo templates require `invoice_external_ref`; invoice templates do not.
3. Service templates require `line_description` and `account_code`.
4. Item templates require `item_code`, `qty`, and `price`.

## Common Validation Errors
1. `Required.`
- A required field is missing.

2. `Duplicate line_no within the same external_ref.`
- Repeated line number inside one grouped document.

3. `Inconsistent invoice-level value for external_ref ...`
- Header-level fields differ across rows of same external_ref.

4. `Already exists for client: ...`
- Invoice external_ref (or memo number in file mode) already exists.

5. `Unknown A/R Invoice external_ref: ...`
- Credit memo points to non-existent invoice external_ref.

6. `Linked invoice customer does not match --customer-code.`
- Linked invoice customer does not align with import run customer context.

7. `No posting period found for date.` or `Posting period is closed.`
- Posting date is not in an open posting period.

8. `Override count must match number of wtax_ids.`
- `wtax_taxable_overrides` or `wtax_amount_overrides` count mismatches `wtax_ids`.

## Quick Authoring Checklist
1. Keep same `external_ref` for rows belonging to one document.
2. Keep header fields identical across rows of same group.
3. Keep `line_no` unique per group.
4. For credit memos, ensure `invoice_external_ref` exists first in invoice data.
5. If any line is WTax applicable, provide valid `wtax_ids`.
6. Import invoices before credit memos.