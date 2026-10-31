from celery import shared_task
from core import models as c_m
from core.core_functions import Core as super_f
from datetime import datetime, timedelta
from decimal import Decimal


@shared_task
def recur_ar():
    print("Here I am AR!.")
    now = datetime.now()

    getAR = c_m.RecDates.objects.filter(
        status=1,
        date__lte=now.date(),
        rt__type=1
    )
    if getAR:
        for inv in getAR:
            if inv.rt.type == 1:
                newAR = c_m.AROINV.objects.get(id=inv.rt.ar.id)
                terms = newAR.code.terms
                due = now + timedelta(days=terms)

                post = c_m.PostingPeriod.objects.filter(
                    from_date__lte=now.date(),
                    to_date__gte=now.date()
                ).first()
                docNo = c_m.DocumentNo.objects.filter(
                    client=inv.rt.client,
                    name='A/R Invoice'
                ).first()
                jeNo = c_m.DocumentNo.objects.filter(
                    client=inv.rt.client,
                    name='Journal Entry'
                ).first()
                client = inv.rt.client
                newInv = int(docNo.no) + 1
                newJE = int(jeNo.no) + 1
                if post:
                    if post.status == 2:
                        mes1 = f"A/R Invoice No. {newAR.invoice_num}"
                        mes2 = "cannot recur today because"
                        mes3 = "the Posting Date is closed."
                        cn = c_m.Notifications.objects.filter(
                            client=client,
                            receiver=newAR.added,
                            message=f"{mes1} {mes2} {mes3}",
                            module="/sales/recurring-transactions"
                        ).exists()
                        if not cn:
                            super_f.add_notif(
                                client=client,
                                receiver=newAR.added,
                                message=f"{mes1} {mes2} {mes3}",
                                module="/sales/recurring-transactions",
                                type=2
                            )
                    else:
                        # print("goods")
                        app = c_m.Approval.objects.get(
                            client=client,
                            module="A/R Invoice Approver"
                        )
                        ver = c_m.Approval.objects.get(
                            client=client,
                            module="A/R Invoice Verifier"
                        )
                        ar = c_m.AROINV(
                            client=client,
                            code=newAR.code,
                            bp_code=newAR.bp_code,
                            bp_name=newAR.bp_name,
                            type=newAR.type,
                            invoice_num=newInv,
                            posting_date=now.date(),
                            due_date=due,
                            doc_date=now.date(),
                            receipt_date=now.date(),
                            po_num=newAR.po_num,
                            remarks=newAR.remarks,
                            price_bef_vat=newAR.price_bef_vat,
                            discount=newAR.discount,
                            vat=newAR.vat,
                            wtax=newAR.wtax,
                            total=newAR.total,
                            added=newAR.added
                        )
                        if ver.status == 1:
                            ar.status = 5
                            end = "is awaiting your verification."
                            mess = f"A/R Invoice {newInv} {end}"
                            super_f.add_notif(
                                client=client,
                                sender=newAR.added,
                                receiver=ver.user,
                                message=mess,
                                module="/approval?module=2",
                                type=2
                            )
                        elif app.status == 1:
                            ar.status = 6
                            end = "is awaiting your approval."
                            mess = f"A/R Invoice {newInv} {end}"
                            super_f.add_notif(
                                client=client,
                                sender=newAR.added,
                                receiver=app.user,
                                message=mess,
                                module="/approval?module=2",
                                type=2
                            )
                        else:
                            ar.status = 1
                        ar.save()

                        for rows in newAR.invRows.all():
                            ar1 = c_m.ARINV1(
                                ar=ar,
                                vatable=rows.vatable,
                                wtax=rows.wtax,
                                amount=rows.amount,
                                customer=rows.customer,
                                discount=rows.discount
                            )
                            if newAR.type == 2:
                                ar1.description = rows.description
                                ar1.account = rows.account
                            else:
                                prod = rows.product
                                ar1.description = prod.name
                                ar1.account = prod.income
                                ar1.product = prod
                                ar1.price = rows.price
                                ar1.qty = rows.qty

                            ar1.save()

                        for rows in newAR.invTax.all():
                            ar2 = c_m.ARINV2(
                                ar=ar,
                                wtax=rows.wtax,
                                name=rows.name,
                                rate=rows.rate,
                                taxable_amt=rows.taxable_amt,
                                wtax_amt=rows.wtax_amt
                            )
                            ar2.save()

                        if ver.status == 2 and app.status == 2:
                            ojdt = c_m.OJDT(
                                client=client,
                                no=newJE,
                                origin=2,
                                origin_no=newInv,
                                remarks=f"Based on A/R Invoice {newInv}",
                                post_date=newAR.posting_date,
                                due_date=due,
                                doc_date=newAR.doc_date,
                                trans_no=ar.id,
                                total=newAR.total
                            )
                            ojdt.save()

                            ar_amt = newAR.total
                            super_f.add_JE(
                                ojdt=ojdt,
                                account=super_f.get_ae(
                                    client=client,
                                    type="A/R Account"
                                ).account,
                                debit=ar_amt,
                                credit=0,
                                remarks="",
                                post_date=newAR.posting_date,
                                customer=newAR.code.id
                            )
                            ar = super_f.get_ae(
                                    client=client,
                                    type="A/R Account"
                                ).account
                            ar.balance += ar_amt
                            ar.save()

                            if newAR.vat > 0:
                                # vat_amt = ar_amt - (ar_amt / Decimal(1.12))
                                vat_amt = newAR.vat
                                super_f.add_JE(
                                    ojdt=ojdt,
                                    account=super_f.get_ae(
                                        client=client,
                                        type="Output VAT"
                                    ).account,
                                    debit=0,
                                    credit=vat_amt,
                                    remarks="",
                                    post_date=newAR.posting_date,
                                    customer=newAR.code.id
                                )
                                vat = super_f.get_ae(
                                        client=client,
                                        type="Output VAT"
                                    ).account
                                vat.balance += vat_amt
                                vat.save()

                            for rows in newAR.invRows.all():
                                ramt = super_f.round2(rows.amount)
                                rdis = super_f.round2(rows.discount)
                                vat = Decimal("1.12")
                                if int(rows.vatable) == 1:
                                    si = (super_f.round2(ramt / vat) - rdis)
                                else:
                                    si = (ramt - rdis)
                                if newAR.type == 2:
                                    super_f.add_JE(
                                        ojdt=ojdt,
                                        account=rows.account,
                                        debit=0,
                                        credit=si,
                                        remarks=rows.description,
                                        post_date=newAR.posting_date,
                                        customer=rows.customer.id
                                    )
                                    acc = rows.account
                                    acc.balance += si
                                    acc.save()
                                else:
                                    prod = rows.product
                                    ae = super_f.get_ae(
                                        client=client,
                                        type="Inventory Account"
                                    )
                                    super_f.add_JE(
                                        ojdt=ojdt,
                                        account=prod.income,
                                        debit=0,
                                        credit=si,
                                        remarks=prod.name,
                                        post_date=newAR.posting_date,
                                        customer=rows.customer.id
                                    )
                                    prod.income.balance += si
                                    prod.income.save()

                                    amt = prod.cost * rows.qty
                                    super_f.add_JE(
                                        ojdt=ojdt,
                                        account=prod.cogs,
                                        debit=amt,
                                        credit=0,
                                        remarks=prod.name,
                                        post_date=newAR.posting_date,
                                        customer=rows.customer.id
                                    )
                                    prod.cogs.balance += si
                                    prod.cogs.save()

                                    super_f.add_JE(
                                        ojdt=ojdt,
                                        account=ae.account,
                                        debit=0,
                                        credit=amt,
                                        remarks=prod.name,
                                        post_date=newAR.posting_date,
                                        customer=rows.customer.id
                                    )
                                    ae.account.balance += si
                                    ae.account.save()

                                    upQ = c_m.Inventory.objects.filter(
                                        id=prod.id
                                    ).first()
                                    qty = rows.qty
                                    upQ.stock -= qty
                                    upQ.save()

                            jeNo.no = newJE
                            jeNo.save()

                        docNo.no = newInv
                        docNo.save()

                    inv.status = 2
                    inv.date_exe = now.date()
                    inv.save()

                else:
                    print("invalid posting date")
                    mes1 = f"A/R Invoice No. {newAR.invoice_num}"
                    mes2 = "cannot recur today because"
                    mes3 = "the Posting Date is invalid."
                    cn = c_m.Notifications.objects.filter(
                        client=client,
                        receiver=newAR.added,
                        message=f"{mes1} {mes2} {mes3}",
                        module="/sales/recurring-transactions"
                    ).exists()
                    if not cn:
                        super_f.add_notif(
                            client=client,
                            receiver=newAR.added,
                            message=f"{mes1} {mes2} {mes3}",
                            module="/sales/recurring-transactions",
                            type=2
                        )


@shared_task
def recur_ap():
    print("Here I am AP!.")
    now = datetime.now()

    getAP = c_m.RecDates.objects.filter(
        status=1,
        date__lte=now.date(),
        rt__type=2
    )
    if getAP:
        for inv in getAP:
            newAP = c_m.APOINV.objects.get(id=inv.rt.ap.id)
            terms = newAP.code.terms
            due = now + timedelta(days=terms)

            post = c_m.PostingPeriod.objects.filter(
                from_date__lte=now.date(),
                to_date__gte=now.date()
            ).first()
            docNo = c_m.DocumentNo.objects.filter(
                client=inv.rt.client,
                name='A/P Invoice'
            ).first()
            jeNo = c_m.DocumentNo.objects.filter(
                client=inv.rt.client,
                name='Journal Entry'
            ).first()
            client = inv.rt.client
            newInv = int(docNo.no) + 1
            newJE = int(jeNo.no) + 1
            if post:
                if post.status == 2:
                    mes1 = f"A/P Invoice No. {newAP.invoice_num}"
                    mes2 = "cannot recur today because"
                    mes3 = "the Posting Date is closed."
                    cn = c_m.Notifications.objects.filter(
                        client=client,
                        receiver=newAP.added,
                        message=f"{mes1} {mes2} {mes3}",
                        module="/purchasing/recurring-transactions"
                    ).exists()
                    if not cn:
                        super_f.add_notif(
                            client=client,
                            receiver=newAP.added,
                            message=f"{mes1} {mes2} {mes3}",
                            module="/purchasing/recurring-transactions",
                            type=2
                        )
                else:
                    # print("goods")
                    app = c_m.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Approver"
                    )
                    ver = c_m.Approval.objects.get(
                        client=client,
                        module="A/P Invoice Verifier"
                    )
                    ar = c_m.APOINV(
                        client=client,
                        code=newAP.code,
                        bp_code=newAP.bp_code,
                        bp_name=newAP.bp_name,
                        type=newAP.type,
                        invoice_num=newInv,
                        posting_date=now.date(),
                        due_date=due,
                        doc_date=now.date(),
                        po_num=newAP.po_num,
                        remarks=newAP.remarks,
                        price_bef_vat=newAP.price_bef_vat,
                        discount=newAP.discount,
                        vat=newAP.vat,
                        wtax=newAP.wtax,
                        total=newAP.total,
                        added=newAP.added
                    )
                    if newAP.type == 1:
                        ar.applied_tax = newAP.wtax
                    if ver.status == 1:
                        ar.status = 5
                        end = "is awaiting your verification."
                        mess = f"A/P Invoice {newInv} {end}"
                        super_f.add_notif(
                            client=client,
                            sender=newAP.added,
                            receiver=ver.user,
                            message=mess,
                            module="/approval?module=4",
                            type=2
                        )
                    elif app.status == 1:
                        ar.status = 6
                        end = "is awaiting your approval."
                        mess = f"A/P Invoice {newInv} {end}"
                        super_f.add_notif(
                            client=client,
                            sender=newAP.added,
                            receiver=app.user,
                            message=mess,
                            module="/approval?module=4",
                            type=2
                        )
                    else:
                        ar.status = 1
                    ar.save()

                    for rows in newAP.invAPRows.all():
                        ar1 = c_m.APINV1(
                            ap=ar,
                            vatable=rows.vatable,
                            wtax=rows.wtax,
                            amount=rows.amount
                        )
                        if newAP.type == 2:
                            ar1.description = rows.description
                            ar1.account = rows.account
                        else:
                            prod = rows.product
                            ar1.description = prod.name
                            ar1.account = rows.account
                            ar1.product = prod
                            ar1.price = rows.price
                            ar1.qty = rows.qty

                        ar1.customer = rows.customer
                        ar1.discount = rows.discount
                        ar1.save()

                    for rows in newAP.invAPTax.all():
                        ar2 = c_m.APINV2(
                            ap=ar,
                            wtax=rows.wtax,
                            name=rows.name,
                            rate=rows.rate,
                            taxable_amt=rows.taxable_amt,
                            wtax_amt=rows.wtax_amt
                        )
                        ar2.save()

                    if ver.status == 2 and app.status == 2:
                        ojdt = c_m.OJDT(
                            client=client,
                            no=newJE,
                            origin=4,
                            origin_no=newInv,
                            remarks=f"Based on A/P Invoice {newInv}",
                            post_date=newAP.posting_date,
                            due_date=due,
                            doc_date=newAP.doc_date,
                            trans_no=ar.id,
                            total=newAP.total
                        )
                        ojdt.save()

                        if newAP.type == 1:
                            ap_amt = (newAP.total - newAP.discount)
                        else:
                            ap_amt = newAP.total
                        super_f.add_JE(
                            ojdt=ojdt,
                            account=super_f.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account,
                            debit=0,
                            credit=ap_amt,
                            remarks="",
                            post_date=newAP.posting_date,
                            customer=newAP.code.id
                        )
                        ar = super_f.get_ae(
                                client=client,
                                type="A/P Account"
                            ).account
                        ar.balance += ap_amt
                        ar.save()

                        for rows in newAP.invAPRows.all():
                            ramt = super_f.round2(rows.amount)
                            rdis = super_f.round2(rows.discount)
                            vat = Decimal("1.12")
                            if rows.vatable == 1:
                                ap = (super_f.round2(ramt / vat) - rdis)
                            else:
                                ap = (ramt - rdis)
                            if newAP.type == 2:
                                super_f.add_JE(
                                    ojdt=ojdt,
                                    account=rows.account,
                                    debit=ap,
                                    credit=0,
                                    remarks=rows.description,
                                    post_date=newAP.posting_date,
                                    customer=rows.customer.id
                                )
                                acc = rows.account
                                acc.balance += ap
                                acc.save()
                            else:
                                prod = rows.product
                                super_f.add_JE(
                                    ojdt=ojdt,
                                    account=rows.account,
                                    debit=ap,
                                    credit=0,
                                    remarks=rows.description,
                                    post_date=newAP.posting_date,
                                    customer=rows.customer.id
                                )
                                acc = rows.account
                                acc.balance += ap
                                acc.save()
                                upQty = c_m.Inventory.objects.get(
                                    id=prod.id
                                )
                                upQty.stock += rows.qty
                                upQty.save()

                        if newAP.vat > 0:
                            super_f.add_JE(
                                ojdt=ojdt,
                                account=super_f.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account,
                                debit=newAP.vat,
                                credit=0,
                                remarks="",
                                post_date=newAP.posting_date,
                                customer=newAP.code.id
                            )
                            vat = super_f.get_ae(
                                    client=client,
                                    type="Input VAT"
                                ).account
                            vat.balance += newAP.vat
                            vat.save()

                        if newAP.type == 1:
                            for rows in newAP.invAPTax.all():
                                super_f.add_JE(
                                    ojdt=ojdt,
                                    account=rows.wtax.account,
                                    debit=0,
                                    credit=rows.wtax_amt,
                                    remarks=rows.wtax.type,
                                    post_date=now.date(),
                                    customer=""
                                )
                                acc1 = rows.wtax.account
                                print(f"ACC1 {acc1}")
                                acc1.balance += rows.wtax_amt
                                acc1.save()

                        jeNo.no = newJE
                        jeNo.save()

                    docNo.no = newInv
                    docNo.save()

                inv.status = 2
                inv.date_exe = now.date()
                inv.save()

            else:
                print("invalid posting date")
                mes1 = f"A/P Invoice No. {newAP.invoice_num}"
                mes2 = "cannot recur today because"
                mes3 = "the Posting Date is invalid."
                cn = c_m.Notifications.objects.filter(
                    client=client,
                    receiver=newAP.added,
                    message=f"{mes1} {mes2} {mes3}",
                    module="/purchasing/recurring-transactions"
                ).exists()
                if not cn:
                    super_f.add_notif(
                        client=client,
                        receiver=newAP.added,
                        message=f"{mes1} {mes2} {mes3}",
                        module="/purchasing/recurring-transactions",
                        type=2
                    )


@shared_task
def close_recur():
    trans = c_m.RecTrans.objects.filter(
        status=1
    )

    for tran in trans:
        invs = c_m.RecDates.objects.filter(
            rt=tran,
            status=1
        )
        if invs.count() == 0:
            tran.status = 2
            tran.save()
