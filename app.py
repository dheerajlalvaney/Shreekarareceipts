import io
import re
from datetime import date

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether
)

st.set_page_config(page_title="Shreekara Donation Receipt", page_icon="🧾", layout="centered")

# Unicode-capable fonts for the Indian rupee symbol in generated PDFs.
pdfmetrics.registerFont(TTFont("NotoSans", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"))

# ---------- Helpers ----------
ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def two_digits(n: int) -> str:
    if n < 20:
        return ONES[n]
    return TENS[n // 10] + (" " + ONES[n % 10] if n % 10 else "")


def three_digits(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(ONES[n // 100] + " Hundred")
        n %= 100
    if n:
        parts.append(two_digits(n))
    return " ".join(parts)


def amount_in_words_indian(amount: float) -> str:
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    if rupees == 0:
        words = "Zero"
    else:
        parts = []
        crore, rupees = divmod(rupees, 10_000_000)
        lakh, rupees = divmod(rupees, 100_000)
        thousand, rupees = divmod(rupees, 1_000)
        hundred_part = rupees
        if crore:
            parts.append(three_digits(crore) + " Crore")
        if lakh:
            parts.append(three_digits(lakh) + " Lakh")
        if thousand:
            parts.append(three_digits(thousand) + " Thousand")
        if hundred_part:
            parts.append(three_digits(hundred_part))
        words = " ".join(parts)
    result = f"Rupees {words}"
    if paise:
        result += f" and {two_digits(paise)} Paise"
    return result + " Only"


def clean_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value or "donation_receipt"


def pdf_receipt(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Donation Receipt {data['receipt_no']}",
        author="Shreekara World Foundation",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FoundationTitle", parent=styles["Title"], alignment=TA_CENTER,
        fontName="NotoSans-Bold", fontSize=16, leading=20, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Heading2"], alignment=TA_CENTER,
        fontName="NotoSans-Bold", fontSize=12, leading=15, spaceAfter=10
    )
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName="NotoSans",
        fontSize=9.5, leading=13, alignment=TA_LEFT
    )
    small = ParagraphStyle(
        "Small", parent=body, fontSize=7.8, leading=10
    )
    centre_small = ParagraphStyle(
        "CentreSmall", parent=small, alignment=TA_CENTER
    )

    story = [
        Paragraph("SHREEKARA WORLD FOUNDATION", title_style),
    ]
    if data.get("registered_office"):
        story.append(Paragraph(data["registered_office"], centre_small))
    if data.get("foundation_pan"):
        story.append(Paragraph(f"PAN: {data['foundation_pan']}", centre_small))
    story.extend([Spacer(1, 5 * mm), Paragraph("DONATION RECEIPT", subtitle_style)])

    header_table = Table([
        [Paragraph(f"<b>Receipt No.:</b> {data['receipt_no']}", body),
         Paragraph(f"<b>Date:</b> {data['receipt_date'].strftime('%d-%m-%Y')}", body)]
    ], colWidths=[85 * mm, 65 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([header_table, Spacer(1, 5 * mm)])

    purpose = data["purpose"]
    if purpose == "Specific Programme":
        purpose = f"Specific Programme - {data.get('programme_name', '').strip()}"

    rows = [
        ["Received with thanks from", data["donor_name"]],
        ["Address", data.get("address") or "-"],
        ["PAN / Identification No.", data.get("donor_pan") or "-"],
        ["Amount", f"₹ {data['amount']:,.2f}"],
        ["Amount in words", amount_in_words_indian(data["amount"])],
        ["Mode of payment", data["payment_mode"]],
        ["Transaction / Cheque reference", data.get("transaction_ref") or "-"],
        ["Date of payment", data["payment_date"].strftime("%d-%m-%Y")],
        ["Purpose of donation", purpose],
    ]
    receipt_table = Table(
        [[Paragraph(f"<b>{label}</b>", body), Paragraph(str(value), body)] for label, value in rows],
        colWidths=[55 * mm, 95 * mm],
        repeatRows=0,
    )
    receipt_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#B7B7B7")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F3F3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([receipt_table, Spacer(1, 5 * mm)])

    story.append(Paragraph(
        "The donation has been received voluntarily and without any consideration in return.", body
    ))
    story.append(Spacer(1, 3 * mm))

    if data.get("is_corpus"):
        story.append(Paragraph(
            "<b>Corpus declaration:</b> This contribution is being acknowledged as a corpus donation "
            "based on the donor's specific written direction that it shall form part of the corpus of the Foundation.",
            small,
        ))
        story.append(Spacer(1, 2 * mm))

    if data.get("show_80g"):
        approval = data.get("approval_80g") or "Not entered"
        validity = data.get("approval_validity") or "Not entered"
        story.append(Paragraph(
            f"<b>80G Registration / Approval No.:</b> {approval}<br/>"
            f"<b>Validity:</b> {validity}", body
        ))
        story.append(Spacer(1, 3 * mm))

    signature = Table([
        ["", Paragraph("For <b>Shreekara World Foundation</b>", body)],
        ["", Spacer(1, 14 * mm)],
        ["", Paragraph("Authorised Signatory", body)],
    ], colWidths=[90 * mm, 60 * mm])
    signature.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([Spacer(1, 3 * mm), signature, Spacer(1, 4 * mm)])

    notes = []
    if data.get("show_80g"):
        notes.append("Deduction under Section 80G is subject to the applicable provisions of the Income-tax Act and the donor's eligibility.")
        notes.append("Donations made in kind are not eligible for deduction under Section 80G.")
    if data.get("is_corpus"):
        notes.append("The donor's written corpus direction should be preserved with the accounting records.")
    if notes:
        story.append(Paragraph("<b>Notes:</b> " + " ".join(notes), small))

    doc.build(story)
    return buffer.getvalue()


def make_register_row(data: dict) -> pd.DataFrame:
    purpose = data["purpose"]
    if purpose == "Specific Programme":
        purpose = f"Specific Programme - {data.get('programme_name', '').strip()}"
    return pd.DataFrame([{
        "Receipt No.": data["receipt_no"],
        "Receipt Date": data["receipt_date"].isoformat(),
        "Donor Name": data["donor_name"],
        "Address": data.get("address", ""),
        "Donor PAN / ID": data.get("donor_pan", ""),
        "Amount": data["amount"],
        "Payment Mode": data["payment_mode"],
        "Transaction Reference": data.get("transaction_ref", ""),
        "Payment Date": data["payment_date"].isoformat(),
        "Purpose": purpose,
        "Corpus Donation": "Yes" if data.get("is_corpus") else "No",
        "80G Receipt": "Yes" if data.get("show_80g") else "No",
    }])


# ---------- UI ----------
st.title("Shreekara Donation Receipt Generator")
st.caption("Generate a PDF donation receipt and maintain a downloadable donor register.")

with st.expander("Foundation settings", expanded=False):
    registered_office = st.text_area("Registered office / address", placeholder="Enter the registered office address")
    foundation_pan = st.text_input("PAN of Shreekara World Foundation")
    show_80g = st.checkbox("Show 80G details on receipt", value=False)
    approval_80g = st.text_input("80G approval / registration number", disabled=not show_80g)
    approval_validity = st.text_input("80G validity", placeholder="e.g. AY 2025-26 to AY 2029-30", disabled=not show_80g)

st.subheader("Receipt details")
col1, col2 = st.columns(2)
with col1:
    receipt_no = st.text_input("Receipt number *", placeholder="SWF/2026-27/001")
with col2:
    receipt_date = st.date_input("Receipt date *", value=date.today())

st.subheader("Donor details")
donor_name = st.text_input("Donor name *", placeholder="Papiya Roy")
address = st.text_area("Address", placeholder="Full postal address")
donor_pan = st.text_input("PAN / Identification number")

st.subheader("Donation details")
col3, col4 = st.columns(2)
with col3:
    amount = st.number_input("Amount (₹) *", min_value=0.0, step=100.0, format="%.2f")
    payment_mode = st.selectbox("Payment mode *", ["UPI", "NEFT", "RTGS", "Cheque", "Cash", "Other"])
with col4:
    payment_date = st.date_input("Payment date *", value=date.today())
    transaction_ref = st.text_input("Transaction / cheque reference")

purpose = st.selectbox("Purpose of donation *", ["General Donation", "Specific Programme", "Corpus Donation"])
programme_name = ""
if purpose == "Specific Programme":
    programme_name = st.text_input("Programme name *")
is_corpus = purpose == "Corpus Donation"
corpus_confirmation = False
if is_corpus:
    corpus_confirmation = st.checkbox(
        "I confirm that written direction from the donor for corpus treatment is available."
    )

st.divider()
register_upload = st.file_uploader(
    "Optional: upload your existing donor register CSV to append this receipt",
    type=["csv"],
    help="The app will append the current receipt and give you an updated CSV to download.",
)

generate = st.button("Generate receipt", type="primary", use_container_width=True)

if generate:
    errors = []
    if not receipt_no.strip(): errors.append("Receipt number is required.")
    if not donor_name.strip(): errors.append("Donor name is required.")
    if amount <= 0: errors.append("Donation amount must be greater than zero.")
    if purpose == "Specific Programme" and not programme_name.strip(): errors.append("Programme name is required.")
    if is_corpus and not corpus_confirmation: errors.append("Confirm that the donor's written corpus direction is available.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        data = {
            "registered_office": registered_office.strip(),
            "foundation_pan": foundation_pan.strip().upper(),
            "show_80g": show_80g,
            "approval_80g": approval_80g.strip(),
            "approval_validity": approval_validity.strip(),
            "receipt_no": receipt_no.strip(),
            "receipt_date": receipt_date,
            "donor_name": donor_name.strip(),
            "address": address.strip(),
            "donor_pan": donor_pan.strip().upper(),
            "amount": float(amount),
            "payment_mode": payment_mode,
            "payment_date": payment_date,
            "transaction_ref": transaction_ref.strip(),
            "purpose": purpose,
            "programme_name": programme_name,
            "is_corpus": is_corpus,
        }
        pdf_bytes = pdf_receipt(data)
        new_row = make_register_row(data)
        if register_upload is not None:
            try:
                old_register = pd.read_csv(register_upload)
                updated_register = pd.concat([old_register, new_row], ignore_index=True)
            except Exception as exc:
                st.warning(f"The uploaded CSV could not be read, so a new register was created. Details: {exc}")
                updated_register = new_row
        else:
            updated_register = new_row

        csv_bytes = updated_register.to_csv(index=False).encode("utf-8-sig")
        base_name = clean_filename(f"{receipt_no}_{donor_name}")

        st.success("Receipt generated successfully.")
        st.download_button(
            "Download PDF receipt",
            data=pdf_bytes,
            file_name=f"{base_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.download_button(
            "Download updated donor register (CSV)",
            data=csv_bytes,
            file_name="Shreekara_Donor_Register.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.dataframe(updated_register.tail(10), use_container_width=True, hide_index=True)

st.info(
    "Important: This starter version does not permanently store data online. Download the updated CSV after each entry, "
    "and upload it the next time you use the app. A later version can connect to Google Sheets or a database."
)
