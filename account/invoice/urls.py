from django.urls import path
from .views import (
    invoice_form_view,
)

urlpatterns = [
    path("invoice/", invoice_form_view, name="invoice-form"),
]