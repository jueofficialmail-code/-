# google_sheet.py

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet(sheet_name: str):
    google_creds = os.getenv("GOOGLE_SA_JSON")

    if not google_creds:
        raise Exception("GOOGLE_SA_JSON not found in environment variables")

    creds_dict = json.loads(google_creds)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet


def write_to_sheet(sheet_name: str, values: list):
    sheet = get_sheet(sheet_name)
    sheet.append_row(values)
