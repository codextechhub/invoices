import base64

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .forms import InvoiceGenerateForm
from .services.invoice_renderer import build_invoice_pdf


@require_http_methods(["GET", "POST"])
def invoice_form_view(request):
    if request.method == "POST":
        form = InvoiceGenerateForm(request.POST)
        if form.is_valid():
            pdf_bytes, invoice_no = build_invoice_pdf(form.cleaned_data)

            request.session["invoice_pdf_base64"] = base64.b64encode(pdf_bytes).decode("utf-8")
            request.session["invoice_number"] = invoice_no
            request.session["invoice_form_data"] = form.cleaned_data

            return redirect("invoice-preview")
    else:
        form = InvoiceGenerateForm()

    return render(request, "invoices/invoice_form.html", {"form": form})


@require_http_methods(["GET"])
def invoice_preview_view(request):
    pdf_base64 = request.session.get("invoice_pdf_base64")
    invoice_number = request.session.get("invoice_number")
    form_data = request.session.get("invoice_form_data")

    if not pdf_base64:
        return redirect("invoice-form")

    pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"

    context = {
        "pdf_data_url": pdf_data_url,
        "invoice_number": invoice_number,
        "form_data": form_data,
    }
    return render(request, "invoices/invoice_preview.html", context)


@require_http_methods(["GET"])
def invoice_download_view(request):
    pdf_base64 = request.session.get("invoice_pdf_base64")
    invoice_number = request.session.get("invoice_number", "invoice")

    if not pdf_base64:
        return redirect("invoice-form")

    pdf_bytes = base64.b64decode(pdf_base64)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice_number}.pdf"'
    return response