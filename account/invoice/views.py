from decimal import Decimal, InvalidOperation

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import InvoiceGenerateForm
from .services.invoice_renderer import build_invoice_pdf_from_payload


def _build_items_from_post(post_data):
    item_names = post_data.getlist("item[]")
    quantities = post_data.getlist("quantity[]")
    prices = post_data.getlist("amount[]")

    items = []
    errors = []

    row_count = max(len(item_names), len(quantities), len(prices))

    for index in range(row_count):
        item_name = item_names[index].strip() if index < len(item_names) else ""
        quantity_raw = quantities[index].strip() if index < len(quantities) else ""
        price_raw = prices[index].strip() if index < len(prices) else ""

        if not item_name and not quantity_raw and not price_raw:
            continue

        if not item_name:
            errors.append(f"Item row {index + 1}: item name is required.")
            continue

        try:
            quantity = int(quantity_raw)
            if quantity < 1:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f"Item row {index + 1}: quantity must be a whole number greater than 0.")
            continue

        try:
            price = Decimal(price_raw)
            if price <= 0:
                raise ValueError
        except (InvalidOperation, TypeError, ValueError):
            errors.append(f"Item row {index + 1}: price must be a valid amount greater than 0.")
            continue

        items.append({
            "item": item_name,
            "quantity": quantity,
            "price": price,
        })

    if not items:
        errors.append("Please add at least one invoice item.")

    return items, errors


@require_http_methods(["GET", "POST"])
def invoice_form_view(request):
    item_errors = []

    if request.method == "POST":
        form = InvoiceGenerateForm(request.POST)
        items, item_errors = _build_items_from_post(request.POST)

        if form.is_valid() and not item_errors:
            payload = {
                **form.cleaned_data,
                "items": items,
            }

            pdf_bytes, invoice_no = build_invoice_pdf_from_payload(payload)

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="invoice-{invoice_no}.pdf"'
            return response
    else:
        form = InvoiceGenerateForm()

    return render(
        request,
        "invoice/invoice_form.html",
        {
            "form": form,
            "item_errors": item_errors,
        },
    )