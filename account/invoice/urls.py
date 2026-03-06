from django.urls import path
from .views import (
    invoice_form_view,
    invoice_preview_view,
    invoice_download_view,
)

urlpatterns = [
    path("invoice/", invoice_form_view, name="invoice-form"),
    path("invoice/preview/", invoice_preview_view, name="invoice-preview"),
    path("invoice/download/", invoice_download_view, name="invoice-download"),
]