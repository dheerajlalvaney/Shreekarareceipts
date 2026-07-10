# Shreekara Donation Receipt Generator

A beginner-friendly Streamlit app for Shreekara World Foundation.

## What it does

- Captures donor and donation details
- Generates a downloadable PDF receipt
- Supports general, programme-specific, and corpus donations
- Shows optional 80G information
- Creates or updates a downloadable donor register in CSV format
- Converts amounts into Indian-numbering words

## Run on your own computer

1. Install Python 3.11 or later.
2. Put these files in one folder.
3. Open Terminal or Command Prompt in that folder.
4. Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The browser will open automatically.

## Host on Streamlit Community Cloud

1. Create a GitHub account.
2. Create a new GitHub repository, for example `shreekara-receipts`.
3. Upload `app.py` and `requirements.txt`.
4. Sign in to Streamlit Community Cloud using GitHub.
5. Click **Create app**.
6. Select the repository, branch, and `app.py`.
7. Click **Deploy**.

## Data storage warning

This starter app does not permanently store donor data on the server. After generating a receipt, download the updated CSV register. On your next use, upload that CSV before generating the next receipt.

For permanent multi-user storage, connect a later version to Google Sheets, Zoho Creator, Supabase, or another database.

## Accounting workflow

After issuing the receipt, record the bank receipt in Zoho Books against the correct generic ledger, such as `General Donations - Domestic`, and associate the donor contact wherever your Zoho workflow permits.

## Compliance note

Use corpus wording only where the donor has provided written direction. Show 80G details only where the Foundation has valid approval. Have the final receipt wording and numbering control reviewed by the Foundation's CA or auditor.
