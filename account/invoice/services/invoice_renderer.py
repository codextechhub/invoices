from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
import io
import os
import random

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


Money = Decimal


@dataclass(frozen=True)
class ContactBlock:
    name: str
    address_line: str
    email: str


@dataclass(frozen=True)
class InvoiceLine:
    item: str
    quantity: int
    price: Money

    @property
    def amount(self) -> Money:
        return (Money(self.quantity) * self.price).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )


@dataclass
class InvoiceDoc:
    invoice_no: str
    invoice_date: date
    billed_to: ContactBlock
    from_block: ContactBlock
    lines: List[InvoiceLine]
    payment_method: str
    note: str
    currency_symbol = "N "

    @property
    def total(self) -> Money:
        s = sum((ln.amount for ln in self.lines), Decimal("0.00"))
        return s.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_fmt(value: Money, currency_symbol: str = "N ") -> str:
    q = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if q == q.to_integral():
        return f"{currency_symbol}{q:,.0f}"
    return f"{currency_symbol}{q:,.2f}"


@dataclass
class InvoiceTheme:
    page_size: Tuple[float, float] = A4
    template_background_path: Optional[str] = None

    text: colors.Color = colors.Color(0.10, 0.10, 0.10)
    light_text: colors.Color = colors.Color(0.25, 0.25, 0.25)
    header_grey: colors.Color = colors.Color(0.92, 0.92, 0.92)
    rule_grey: colors.Color = colors.Color(0.82, 0.82, 0.82)
    wave_light: colors.Color = colors.Color(0.83, 0.83, 0.83)
    wave_dark: colors.Color = colors.Color(0.26, 0.27, 0.27)

    font_reg: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"

    margin_left: float = 20 * mm
    margin_right: float = 20 * mm
    margin_top: float = 18 * mm

    wave_y_shift_mm: float = -70.0
    table_top_offset_mm: float = 120.0
    payment_block_gap_mm: float = 10.0
    billed_from_offset_mm: float = 92.0

    logo_label: str = "YOUR\nLOGO"
    title_text: str = "INVOICE"
    logo_path: Optional[str] = None


class InvoiceRenderer:
    def __init__(self, theme: InvoiceTheme):
        self.t = theme
        self._after_table_y = None

    def render_to_bytes(self, doc: InvoiceDoc) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.t.page_size)
        W, H = self.t.page_size

        if self.t.template_background_path:
            c.drawImage(self.t.template_background_path, 0, 0, width=W, height=H, mask="auto")
        else:
            self._draw_background_waves(c, W, H)

        self._draw_top_row(c, doc, W, H)
        self._draw_title_and_date(c, doc, W, H)
        self._draw_billed_from_blocks(c, doc, W, H)
        self._draw_items_table(c, doc, W, H)
        self._draw_payment_and_note(c, doc, W, H)

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _draw_top_row(self, c: canvas.Canvas, doc: InvoiceDoc, W: float, H: float) -> None:
        xL = self.t.margin_left
        xR = W - self.t.margin_right
        y = H - self.t.margin_top

        if self.t.logo_path and os.path.exists(self.t.logo_path):
            c.drawImage(
                self.t.logo_path,
                xL, y - 22,
                width=32 * mm, height=18 * mm,
                preserveAspectRatio=True,
                mask="auto"
            )
        else:
            c.setFillColor(self.t.light_text)
            c.setFont(self.t.font_reg, 12)
            for i, line in enumerate(self.t.logo_label.split("\n")):
                c.drawString(xL, y - i * 14, line)

        c.setFont(self.t.font_reg, 12)
        c.drawRightString(xR, y, f"NO. {doc.invoice_no}")

    def _draw_title_and_date(self, c: canvas.Canvas, doc: InvoiceDoc, W: float, H: float) -> None:
        xL = self.t.margin_left
        y_title = H - self.t.margin_top - 48 * mm

        c.setFillColor(self.t.text)
        c.setFont(self.t.font_bold, 64)
        c.drawString(xL, y_title, self.t.title_text)

        y_date = y_title - 20 * mm
        c.setFont(self.t.font_bold, 14)
        c.drawString(xL, y_date, "Date:")
        c.setFont(self.t.font_reg, 14)
        c.drawString(xL + 22 * mm, y_date, doc.invoice_date.strftime("%d %B %Y"))

    def _draw_billed_from_blocks(self, c: canvas.Canvas, doc: InvoiceDoc, W: float, H: float) -> None:
        xL = self.t.margin_left
        xMid = W * 0.56
        y0 = H - self.t.margin_top - (self.t.billed_from_offset_mm * mm)

        c.setFillColor(self.t.text)
        c.setFont(self.t.font_bold, 14)
        c.drawString(xL, y0, "Billed to:")
        c.setFont(self.t.font_reg, 14)
        c.drawString(xL, y0 - 16, doc.billed_to.name)
        c.drawString(xL, y0 - 32, doc.billed_to.address_line)
        c.drawString(xL, y0 - 48, doc.billed_to.email)

        c.setFont(self.t.font_bold, 14)
        c.drawString(xMid, y0, "From:")
        c.setFont(self.t.font_reg, 14)
        c.drawString(xMid, y0 - 16, doc.from_block.name)
        c.drawString(xMid, y0 - 32, doc.from_block.address_line)
        c.drawString(xMid, y0 - 48, doc.from_block.email)

    def _draw_items_table(self, c: canvas.Canvas, doc: InvoiceDoc, W: float, H: float) -> None:
        xL = self.t.margin_left
        xR = W - self.t.margin_right
        table_top = H - self.t.margin_top - (self.t.table_top_offset_mm * mm)
        row_h = 14 * mm

        col_item_w = (xR - xL) * 0.48
        col_qty_w = (xR - xL) * 0.17
        col_price_w = (xR - xL) * 0.17

        x_item = xL
        x_qty = x_item + col_item_w
        x_price = x_qty + col_qty_w

        c.setFillColor(self.t.header_grey)
        c.rect(xL, table_top - row_h, xR - xL, row_h, stroke=0, fill=1)

        c.setFillColor(self.t.text)
        c.setFont(self.t.font_reg, 14)
        c.drawString(x_item + 10 * mm, table_top - 0.70 * row_h, "Item")
        c.drawString(x_qty + 2 * mm, table_top - 0.70 * row_h, "Quantity")
        c.drawString(x_price + 2 * mm, table_top - 0.70 * row_h, "Price")
        c.drawRightString(xR - 10 * mm, table_top - 0.70 * row_h, "Amount")

        y = table_top - row_h - 6 * mm
        c.setFont(self.t.font_reg, 14)

        for ln in doc.lines:
            y -= 12 * mm
            c.drawString(x_item + 10 * mm, y, ln.item[:40])
            c.drawString(x_qty + 12 * mm, y, str(ln.quantity))
            c.drawRightString(x_price + col_price_w - 10 * mm, y, money_fmt(ln.price, doc.currency_symbol))
            c.drawRightString(xR - 10 * mm, y, money_fmt(ln.amount, doc.currency_symbol))

        div_y = y - 10 * mm
        c.setStrokeColor(self.t.rule_grey)
        c.setLineWidth(2)
        c.line(xL + 6 * mm, div_y, xR - 6 * mm, div_y)

        total_y = div_y - 14 * mm
        c.setFillColor(self.t.text)
        c.setFont(self.t.font_bold, 16)
        c.drawString(x_price + 10 * mm, total_y, "Total")
        c.drawRightString(xR - 10 * mm, total_y, money_fmt(doc.total, doc.currency_symbol))

        bot_div_y = total_y - 10 * mm
        c.setStrokeColor(self.t.rule_grey)
        c.setLineWidth(2)
        c.line(xL + 6 * mm, bot_div_y, xR - 6 * mm, bot_div_y)

        self._after_table_y = bot_div_y

    def _draw_payment_and_note(self, c: canvas.Canvas, doc: InvoiceDoc, W: float, H: float) -> None:
        xL = self.t.margin_left
        y = (self._after_table_y or (H * 0.35)) - (self.t.payment_block_gap_mm * mm)

        c.setFillColor(self.t.text)

        c.setFont(self.t.font_bold, 14)
        c.drawString(xL, y, "Payment method:")
        c.setFont(self.t.font_reg, 14)
        c.drawString(xL + 48 * mm, y, doc.payment_method[:75])

        y -= 10 * mm
        c.setFont(self.t.font_bold, 14)
        c.drawString(xL, y, "Note:")
        c.setFont(self.t.font_reg, 14)
        c.drawString(xL + 18 * mm, y, doc.note[:90])

    def _draw_background_waves(self, c: canvas.Canvas, W: float, H: float) -> None:
        y_shift = self.t.wave_y_shift_mm * mm

        c.setFillColor(self.t.wave_light)
        p = c.beginPath()
        p.moveTo(0, 0 + y_shift)
        p.lineTo(0, 88 * mm + y_shift)
        p.curveTo(W * 0.18, 140 * mm + y_shift, W * 0.40, 120 * mm + y_shift, W * 0.58, 90 * mm + y_shift)
        p.curveTo(W * 0.74, 65 * mm + y_shift, W * 0.82, 40 * mm + y_shift, W * 0.92, 0 + y_shift)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        c.setFillColor(self.t.wave_dark)
        p2 = c.beginPath()
        p2.moveTo(0, 0 + y_shift)
        p2.lineTo(0, 38 * mm + y_shift)
        p2.curveTo(W * 0.22, 70 * mm + y_shift, W * 0.48, 58 * mm + y_shift, W * 0.62, 40 * mm + y_shift)
        p2.curveTo(W * 0.76, 22 * mm + y_shift, W * 0.86, 35 * mm + y_shift, W, 110 * mm + y_shift)
        p2.lineTo(W, 0 + y_shift)
        p2.close()
        c.drawPath(p2, fill=1, stroke=0)


def generate_invoice_number() -> str:
    return str(random.randint(100001, 999999))


def build_payment_method_sentence(payment_type: str, account_number: str, account_bank: str, account_name: str) -> str:
    return f"{payment_type} [{account_number} - {account_bank} - {account_name}]"


def build_invoice_pdf_from_payload(payload: dict) -> tuple[bytes, str]:
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo-watermark.jpg")
    invoice_no = generate_invoice_number()

    billed_to = ContactBlock(
        name=payload["billed_to_name"],
        address_line=payload["billed_to_address"],
        email=payload["billed_to_email"],
    )

    from_block = ContactBlock(
        name=payload["from_name"],
        address_line=payload["from_address"],
        email=payload["from_email"],
    )

    lines = [
        InvoiceLine(
            item=item["item"],
            quantity=item["quantity"],
            price=item["price"],
        )
        for item in payload["items"]
    ]

    payment_method = build_payment_method_sentence(
        payment_type=payload["payment_type"],
        account_number=payload["account_number"],
        account_bank=payload["account_bank"],
        account_name=payload["account_name"],
    )

    doc = InvoiceDoc(
        invoice_no=invoice_no,
        invoice_date=date.today(),
        billed_to=billed_to,
        from_block=from_block,
        lines=lines,
        payment_method=payment_method,
        note=payload["note"],
    )

    theme = InvoiceTheme(
        wave_y_shift_mm=-70.0,
        table_top_offset_mm=120.0,
        payment_block_gap_mm=10.0,
        logo_path=logo_path,
    )

    pdf_bytes = InvoiceRenderer(theme).render_to_bytes(doc)
    return pdf_bytes, invoice_no