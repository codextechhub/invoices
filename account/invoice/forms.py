from django import forms
from django.core.validators import RegexValidator

PAYMENT_TYPE_CHOICES = [
    ("Transfer", "Transfer"),
    ("Cash", "Cash"),
    ("Card", "Card"),
    ("POS", "POS"),
    ("Mobile Money", "Mobile Money"),
]

BANK_CHOICES = [
    ("Access Bank", "Access Bank"),
    ("Guaranty Trust Bank (GTBank)", "Guaranty Trust Bank (GTBank)"),
    ("OPay", "OPay"),
    ("First Bank", "First Bank"),
    ("Zenith Bank", "Zenith Bank"),
    ("United Bank for Africa (UBA)", "United Bank for Africa (UBA)"),
    ("Moniepoint", "Moniepoint"),
    ("Stanbic IBTC Bank", "Stanbic IBTC Bank"),
    ("Standard Chartered Bank", "Standard Chartered Bank"),
    ("Sterling Bank", "Sterling Bank"),
    ("Citibank Nigeria", "Citibank Nigeria"),
    ("Ecobank", "Ecobank"),
    ("Fidelity Bank", "Fidelity Bank"),
    ("First City Monument Bank (FCMB)", "First City Monument Bank (FCMB)"),
    ("Globus Bank", "Globus Bank"),
    ("Keystone Bank", "Keystone Bank"),
    ("Lotus Bank", "Lotus Bank"),
    ("Nova Merchant Bank", "Nova Merchant Bank"),
    ("Optimus Bank", "Optimus Bank"),
    ("Parallex Bank", "Parallex Bank"),
    ("Polaris Bank", "Polaris Bank"),
    ("PremiumTrust Bank", "PremiumTrust Bank"),
    ("Providus Bank", "Providus Bank"),
    ("Signature Bank", "Signature Bank"),
    ("SunTrust Bank", "SunTrust Bank"),
    ("Titan Trust Bank", "Titan Trust Bank"),
    ("Union Bank", "Union Bank"),
    ("Unity Bank", "Unity Bank"),
    ("Wema Bank", "Wema Bank"),
    ("PalmPay", "PalmPay"),
    ("Kuda", "Kuda"),
]

class InvoiceGenerateForm(forms.Form):
    billed_to_name = forms.CharField(
        max_length=150,
        initial="CodeX Nigeria",
        help_text="The company or individual being billed.",
    )
    billed_to_address = forms.CharField(
        max_length=255,
        initial="Lagos",
        help_text="The address of the company or individual being billed."
    )
    billed_to_email = forms.EmailField(
        initial="accounts@codexng.com",
        help_text="The email of the company or individual being billed."
    )

    from_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="The name of the company or individual sending the invoice.",
        widget=forms.TextInput(attrs={"placeholder": "Your Name"})
    )
    from_address = forms.CharField(
        max_length=255,
        required=False,
        help_text="The address of the company or individual sending the invoice.",
        widget=forms.TextInput(attrs={"placeholder": "Your Address"})
    )
    from_email = forms.EmailField(
        required=False,
        help_text="The email of the company or individual sending the invoice.",
        widget=forms.EmailInput(attrs={"placeholder": "Your Email"})
    )

    payment_type = forms.ChoiceField(
        choices=PAYMENT_TYPE_CHOICES,
        initial="Transfer"
    )
    account_number = forms.CharField(
        max_length=10,
        min_length=10,
        help_text="Enter a 10-digit Nigerian account number.",
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Account number must be exactly 10 digits."
            )
        ],
        widget=forms.TextInput(attrs={
            "placeholder": "Your 10-digit Account Number",
            "inputmode": "numeric",
            "maxlength": "10",
            "pattern": r"\d{10}",
        })
    )
    account_bank = forms.ChoiceField(
        choices=BANK_CHOICES,
        help_text="Select the bank or fintech linked to the account number.",
    )
    account_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="The name associated with your account number.",
        widget=forms.TextInput(attrs={"placeholder": "Your Account Name"})
    )

    note = forms.CharField(
        max_length=255,
        required=False,
        initial="Thank you for investing in CodeX!",
        widget=forms.TextInput(attrs={"placeholder": "Optional note"})
    )