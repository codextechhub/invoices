from django import forms


PAYMENT_TYPE_CHOICES = [
    ("Transfer", "Transfer"),
    ("Cash", "Cash"),
    ("Card", "Card"),
    ("POS", "POS"),
    ("Mobile Money", "Mobile Money"),
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
        max_length=30,
        required=True,
        help_text="Your bank account number for payment.",
        widget=forms.TextInput(attrs={"placeholder": "Your Account Number"})
    )
    account_bank = forms.CharField(
        max_length=100,
        required=True,
        help_text="The bank associated with your account number.",
        widget=forms.TextInput(attrs={"placeholder": "Your Bank Name"})
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