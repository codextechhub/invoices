from __future__ import annotations

import io
import os
import random
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, List

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# -------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------

@dataclass
class ContactBlock:
    name: str
    address_line: str
    email: str = ""


@dataclass
class InvoiceLine:
    description: str
    qty: Decimal
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.qty * self.unit_price


@dataclass
class InvoiceDoc:
    invoice_no: str
    invoice_date: date
    billed_to: ContactBlock
    sender: ContactBlock
    lines: List[InvoiceLine] = field(default_factory=list)
    note: str = ""
    bank_name: str = ""
    account_number: str = ""
    payment_method: str = ""

    @property
    def subtotal(self) -> Decimal:
        return sum((line.line_total for line in self.lines), Decimal("0.00"))

    @property
    def total(self) -> Decimal:
        return self.subtotal


@dataclass
class InvoiceTheme:
    accent_color: tuple = (52/255, 86/255, 149/255)  # close to your blue logo tone
    text_dark: tuple = (0.12, 0.12, 0.12)
    text_muted: tuple = (0.42, 0.42, 0.42)
    border_light: tuple = (0.88, 0.88, 0.88)
    page_background: tuple = (1, 1, 1)
    logo_path: Optional[str] = None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def format_money(value: Decimal) -> str:
    return f"₦{value:,.2f}"


def generate_invoice_number() -> str:
    return f"INV-{date.today().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


# -------------------------------------------------------------------
# Renderer
# -------------------------------------------------------------------

class InvoiceRenderer:
    def __init__(self, doc: InvoiceDoc, theme: InvoiceTheme):
        self.doc = doc
        self.theme = theme
        self.buffer = io.BytesIO()

    def build_pdf_bytes(self) -> bytes:
        c = canvas.Canvas(self.buffer, pagesize=A4)
        width, height = A4

        self.draw_background(c, width, height)
        self.draw_header(c, width, height)
        self.draw_invoice_meta(c, width, height)
        self.draw_contact_blocks(c, width, height)
        self.draw_lines_table(c, width, height)
        self.draw_payment_section(c, width, height)
        self.draw_footer(c, width, height)

        c.showPage()
        c.save()
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf

    def draw_background(self, c, width, height):
        c.setFillColorRGB(*self.theme.page_background)
        c.rect(0, 0, width, height, fill=1, stroke=0)

    def draw_header(self, c, width, height):
        top_y = height - 35 * mm

        if self.theme.logo_path and os.path.exists(self.theme.logo_path):
            try:
                logo = ImageReader(self.theme.logo_path)
                c.drawImage(logo, 18 * mm, top_y - 5 * mm, width=28 * mm, height=28 * mm, mask='auto')
            except Exception:
                pass

        c.setFillColorRGB(*self.theme.accent_color)
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(width - 18 * mm, top_y + 5 * mm, "INVOICE")

        c.setStrokeColorRGB(*self.theme.border_light)
        c.setLineWidth(1)
        c.line(18 * mm, top_y - 10 * mm, width - 18 * mm, top_y - 10 * mm)

    def draw_invoice_meta(self, c, width, height):
        x = width - 75 * mm
        y = height - 55 * mm

        c.setFont("Helvetica", 10)
        c.setFillColorRGB(*self.theme.text_muted)
        c.drawString(x, y, "Invoice No:")
        c.drawString(x, y - 7 * mm, "Date:")

        c.setFillColorRGB(*self.theme.text_dark)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 28 * mm, y, self.doc.invoice_no)
        c.drawString(x + 28 * mm, y - 7 * mm, self.doc.invoice_date.strftime("%d %b %Y"))

    def draw_contact_blocks(self, c, width, height):
        left_x = 18 * mm
        right_x = 105 * mm
        y = height - 85 * mm

        # Billed To
        c.setFillColorRGB(*self.theme.accent_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_x, y, "Billed To")

        c.setFillColorRGB(*self.theme.text_dark)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_x, y - 8 * mm, self.doc.billed_to.name)
        c.setFont("Helvetica", 9)
        c.drawString(left_x, y - 14 * mm, self.doc.billed_to.address_line[:70])
        if self.doc.billed_to.email:
            c.drawString(left_x, y - 20 * mm, self.doc.billed_to.email)

        # From
        c.setFillColorRGB(*self.theme.accent_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(right_x, y, "From")

        c.setFillColorRGB(*self.theme.text_dark)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x, y - 8 * mm, self.doc.sender.name)
        c.setFont("Helvetica", 9)
        c.drawString(right_x, y - 14 * mm, self.doc.sender.address_line[:70])
        if self.doc.sender.email:
            c.drawString(right_x, y - 20 * mm, self.doc.sender.email)

    def draw_lines_table(self, c, width, height):
        table_x = 18 * mm
        table_y = height - 125 * mm
        table_w = width - 36 * mm
        row_h = 10 * mm

        # Header
        c.setFillColorRGB(*self.theme.accent_color)
        c.rect(table_x, table_y, table_w, row_h, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(table_x + 4 * mm, table_y + 3.2 * mm, "Description")
        c.drawString(table_x + 105 * mm, table_y + 3.2 * mm, "Qty")
        c.drawString(table_x + 125 * mm, table_y + 3.2 * mm, "Unit Price")
        c.drawString(table_x + 160 * mm, table_y + 3.2 * mm, "Total")

        current_y = table_y - row_h

        c.setStrokeColorRGB(*self.theme.border_light)
        c.setFillColorRGB(1, 1, 1)

        for line in self.doc.lines:
            c.rect(table_x, current_y, table_w, row_h, fill=1, stroke=1)

            c.setFillColorRGB(*self.theme.text_dark)
            c.setFont("Helvetica", 9)
            c.drawString(table_x + 4 * mm, current_y + 3.2 * mm, line.description[:45])
            c.drawString(table_x + 107 * mm, current_y + 3.2 * mm, f"{line.qty}")
            c.drawRightString(table_x + 157 * mm, current_y + 3.2 * mm, format_money(line.unit_price))
            c.drawRightString(table_x + 191 * mm, current_y + 3.2 * mm, format_money(line.line_total))

            current_y -= row_h

        # Total box
        total_y = current_y - 8 * mm
        c.setFillColorRGB(*self.theme.accent_color)
        c.rect(table_x + 130 * mm, total_y, 62 * mm, 12 * mm, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(table_x + 135 * mm, total_y + 4 * mm, "Total")
        c.drawRightString(table_x + 187 * mm, total_y + 4 * mm, format_money(self.doc.total))

    def draw_payment_section(self, c, width, height):
        y = height - 215 * mm
        x = 18 * mm

        c.setFillColorRGB(*self.theme.accent_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Payment Details")

        c.setFillColorRGB(*self.theme.text_dark)
        c.setFont("Helvetica", 9)
        c.drawString(x, y - 8 * mm, f"Bank Name: {self.doc.bank_name}")
        c.drawString(x, y - 15 * mm, f"Account Number: {self.doc.account_number}")
        c.drawString(x, y - 22 * mm, f"Payment Method: {self.doc.payment_method}")

        if self.doc.note:
            c.setFillColorRGB(*self.theme.accent_color)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y - 35 * mm, "Note")

            c.setFillColorRGB(*self.theme.text_dark)
            c.setFont("Helvetica", 9)
            c.drawString(x, y - 43 * mm, self.doc.note[:100])

    def draw_footer(self, c, width, height):
        c.setStrokeColorRGB(*self.theme.border_light)
        c.line(18 * mm, 20 * mm, width - 18 * mm, 20 * mm)

        c.setFillColorRGB(*self.theme.text_muted)
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, 14 * mm, "Generated by CodeX Invoice Portal")


def build_invoice_pdf(form_data: dict) -> tuple[bytes, str]:
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo-watermark.jpg")

    invoice_no = generate_invoice_number()

    billed_to = ContactBlock(
        name=form_data["billed_to_name"],
        address_line=form_data["billed_to_address"],
        email=form_data.get("billed_to_email", ""),
    )

    sender = ContactBlock(
        name=form_data["from_name"],
        address_line=form_data["from_address"],
        email=form_data.get("from_email", ""),
    )

    amount = Decimal(form_data["amount"])

    doc = InvoiceDoc(
        invoice_no=invoice_no,
        invoice_date=date.today(),
        billed_to=billed_to,
        sender=sender,
        lines=[
            InvoiceLine(
                description="Payment",
                qty=Decimal("1"),
                unit_price=amount,
            )
        ],
        note=form_data.get("note", ""),
        bank_name=form_data["bank_name"],
        account_number=form_data["account_number"],
        payment_method=form_data["payment_method"],
    )

    theme = InvoiceTheme(logo_path=logo_path)
    renderer = InvoiceRenderer(doc=doc, theme=theme)
    pdf_bytes = renderer.build_pdf_bytes()

    return pdf_bytes, invoice_no