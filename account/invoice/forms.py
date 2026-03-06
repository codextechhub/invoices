from decimal import Decimal
from django import forms


PAYMENT_METHOD_CHOICES = [
    ("bank_transfer", "Bank Transfer"),
    ("cash", "Cash"),
    ("card", "Card"),
    ("pos", "POS"),
    ("mobile_money", "Mobile Money"),
    ("other", "Other"),
]


class InvoiceGenerateForm(forms.Form):
    # Billed To
    billed_to_name = forms.CharField(max_length=150)
    billed_to_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    billed_to_email = forms.EmailField(required=False)

    # From
    from_name = forms.CharField(max_length=150, initial="CodeX")
    from_address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        initial="CodeX Nigeria"
    )
    from_email = forms.EmailField(required=False, initial="accounts@codexng.com")

    # Payment details
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    account_number = forms.CharField(max_length=30)
    bank_name = forms.CharField(max_length=120)
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Optional note or narration"
    )

    def clean_account_number(self):
        value = self.cleaned_data["account_number"].strip()
        if not value.replace("-", "").replace(" ", "").isdigit():
            raise forms.ValidationError("Account number should contain only digits, spaces, or hyphens.")
        return value