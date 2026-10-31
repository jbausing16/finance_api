# User Manual: Historical Insertion of Item/Service Invoices with Credit Memos

## Purpose
This guide explains how to import the generated sample seed files for:
- A/R Invoice (Item)
- A/R Invoice (Service)
- A/R Credit Memo (Item)
- A/R Credit Memo (Service)

The files in this folder are partitioned by customer code and doc type.

## Folder
All sample files are in:
- `app/core/management/templates/sample_seed`

## Field-By-Field CSV Guide
For detailed column documentation of all four templates (invoice item/service and credit memo item/service), see:
- `app/core/management/templates/sample_seed/CSV_TEMPLATE_FIELD_GUIDE.md`

## Prerequisites
1. Run from `finance_api` project root.
2. Containers are up:
   - `docker-compose up -d`
3. Required setup data exists for target client:
   - Posting Period (open)
   - Customer codes used in file names (example: `C0001`, `C0003`)
   - DocumentNo (`A/R Invoice`, `A/R Credit Memo`, `Journal Entry`)
   - AutoEntries (`A/R Account`, `Output VAT`, `Inventory Account` for item docs)
4. If re-running the same files, clear previous inserted bulk data first to avoid duplicate `external_ref` errors:
   - `docker-compose exec -it app python manage.py reset_data_bulk`

## Important Rule
Always import in this order:
1. Invoice Item
2. Invoice Service
3. Credit Memo Item
4. Credit Memo Service

Run this per customer partition (for example `C0001` then `C0003`).

## Path Note (Host vs Container)
When you pick files from host path:
- Host path starts with `app/...`

For `--file` argument inside container, remove `app/` prefix:
- Example host: `app/core/management/templates/sample_seed/xxx.csv`
- Example command `--file`: `core/management/templates/sample_seed/xxx.csv`

## 1) Dry-Run Commands (Recommended)
Use this script from `finance_api` root:

```bash
set -e
cd "c:/Users/IT-JAPS/Documents/FINANCE_GAB/finance_api"

for CUST in C0001 C0003; do
  ITEM_INV_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-1_invoice-item.csv | head -n 1)
  SVC_INV_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-2_invoice-service.csv | head -n 1)
  ITEM_CM_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-1_credit-memo-item.csv | head -n 1)
  SVC_CM_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-2_credit-memo-service.csv | head -n 1)

  ITEM_INV_FILE=${ITEM_INV_HOST#app/}
  SVC_INV_FILE=${SVC_INV_HOST#app/}
  ITEM_CM_FILE=${ITEM_CM_HOST#app/}
  SVC_CM_FILE=${SVC_CM_HOST#app/}

  echo "Dry-run Invoice Item: $CUST"
  docker-compose exec -T app python manage.py import_ar_invoice_history \
    --file "$ITEM_INV_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 1 --dry-run

  echo "Dry-run Invoice Service: $CUST"
  docker-compose exec -T app python manage.py import_ar_invoice_history \
    --file "$SVC_INV_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 2 --dry-run

  echo "Dry-run CM Item: $CUST"
  docker-compose exec -T app python manage.py import_ar_credit_memo_history \
    --file "$ITEM_CM_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 1 --dry-run

  echo "Dry-run CM Service: $CUST"
  docker-compose exec -T app python manage.py import_ar_credit_memo_history \
    --file "$SVC_CM_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 2 --dry-run
done
```

## 2) Actual Insert Commands
Run only after all dry-runs pass:

```bash
set -e
cd "c:/Users/IT-JAPS/Documents/FINANCE_GAB/finance_api"

for CUST in C0001 C0003; do
  ITEM_INV_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-1_invoice-item.csv | head -n 1)
  SVC_INV_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-2_invoice-service.csv | head -n 1)
  ITEM_CM_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-1_credit-memo-item.csv | head -n 1)
  SVC_CM_HOST=$(ls app/core/management/templates/sample_seed/*customer-code-${CUST}_doc-type-2_credit-memo-service.csv | head -n 1)

  ITEM_INV_FILE=${ITEM_INV_HOST#app/}
  SVC_INV_FILE=${SVC_INV_HOST#app/}
  ITEM_CM_FILE=${ITEM_CM_HOST#app/}
  SVC_CM_FILE=${SVC_CM_HOST#app/}

  # Invoices first
  docker-compose exec -T app python manage.py import_ar_invoice_history \
    --file "$ITEM_INV_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 1

  docker-compose exec -T app python manage.py import_ar_invoice_history \
    --file "$SVC_INV_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 2

  # Credit memos after invoices
  docker-compose exec -T app python manage.py import_ar_credit_memo_history \
    --file "$ITEM_CM_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 1

  docker-compose exec -T app python manage.py import_ar_credit_memo_history \
    --file "$SVC_CM_FILE" --client-id 1 --actor-useracc-id 2 --customer-code "$CUST" --doc-type 2
done
```

## Optional: Use `--user` Instead of `--actor-useracc-id`
You may replace:
- `--client-id 1 --actor-useracc-id 2`

with:
- `--user alexandra.bausing@gmail.com`

If multiple `UserAcc` match that email, also pass `--client-id` or `--actor-useracc-id` to disambiguate.

## 3) Post-Insert Verification
Check inserted sample counts and status distribution:

```bash
docker-compose exec -T app python manage.py shell -c "
from collections import Counter
from core.models import AROINV, AROCRM
inv = AROINV.objects.filter(client_id=1, external_ref__startswith='MCUST-AR-')
cm = AROCRM.objects.filter(client_id=1, invoice_num__startswith='MC2-CM-')
print({
  'invoice_count': inv.count(),
  'invoice_status': dict(Counter(inv.values_list('status', flat=True))),
  'cm_count': cm.count(),
  'cm_status': dict(Counter(cm.values_list('status', flat=True))),
  'invoice_customers': sorted(set(inv.values_list('bp_code', flat=True)))
})
"
```

## Common Errors and Fixes
1. `Input file not found`
- Use `core/...` path (remove `app/` prefix for `--file`).

2. `Already exists for client: <external_ref>`
- Data already imported. Run `reset_data_bulk` or regenerate refs.

3. `Unknown --customer-code for client`
- Customer does not exist or not type=Customer for that client.

4. `Unknown A/R Invoice external_ref` (during CM import)
- Invoices were not inserted yet, or wrong customer/doc-type file used.

5. `Posting period is closed` or `No posting period found`
- Adjust posting dates in files or open/create posting period.

## Notes
- CSV and XLSX variants are both supported by import commands.
- This seed pack is intended for historical import workflows.
