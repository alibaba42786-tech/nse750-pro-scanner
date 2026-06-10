import os
import json
import pandas as pd
import requests
import gspread
import requests_cache

from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

# =========================================================
# CACHE SYSTEM
# =========================================================

requests_cache.install_cache(
    'nse_cache',
    expire_after=3600
)

# =========================================================
# GOOGLE AUTH
# =========================================================

creds_dict = json.loads(
    os.environ['GOOGLE_CREDS']
)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=scopes
)

client = gspread.authorize(creds)

# =========================================================
# CREATE / OPEN SHEET
# =========================================================

sheet_name = os.environ['SHEET_NAME']

try:
    spreadsheet = client.open(sheet_name)

except:
    spreadsheet = client.create(sheet_name)

# =========================================================
# REQUIRED SHEETS
# =========================================================

required_tabs = [
    "MASTER",
    "FUNDAMENTAL_TOP300",
    "BUY_NOW_50",
    "WATCHLIST",
    "VCP_SCANNER",
    "CPR_BREAKOUT",
    "STAGE2",
    "MARKET_BREADTH",
    "ALERTS_LOG",
    "SETTINGS",
    "CACHE_INFO"
]

existing_tabs = [
    ws.title for ws in spreadsheet.worksheets()
]

for tab in required_tabs:

    if tab not in existing_tabs:
        spreadsheet.add_worksheet(
            title=tab,
            rows=1000,
            cols=50
        )

# =========================================================
# NSE SYMBOL FETCH
# =========================================================

print("Fetching NSE universe...")

n500 = pd.read_csv(
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
)

mid150 = pd.read_csv(
    "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv"
)

small250 = pd.read_csv(
    "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv"
)

symbols = pd.concat([
    n500['Symbol'],
    mid150['Symbol'],
    small250['Symbol']
])

symbols = symbols.drop_duplicates()

stocks = [x + ".NS" for x in symbols]

df = pd.DataFrame({
    "SYMBOL": stocks
})

print(f"Total Stocks: {len(df)}")

# =========================================================
# UPLOAD TO MASTER
# =========================================================

master = spreadsheet.worksheet("MASTER")

master.clear()

set_with_dataframe(
    master,
    df
)

# =========================================================
# HEADER FORMAT
# =========================================================

master.format(
    'A1:Z1',
    {
        "backgroundColor": {
            "red": 0.05,
            "green": 0.05,
            "blue": 0.2
        },
        "textFormat": {
            "foregroundColor": {
                "red": 1,
                "green": 1,
                "blue": 1
            },
            "fontSize": 11,
            "bold": True
        }
    }
)

# =========================================================
# FREEZE HEADER
# =========================================================

master.freeze(rows=1)

# =========================================================
# AUTO WIDTH
# =========================================================

spreadsheet.batch_update({
    "requests": [
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": master.id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 5
                }
            }
        }
    ]
})

print("MASTER SHEET UPDATED")

# =========================================================
# SETTINGS PAGE
# =========================================================

settings = spreadsheet.worksheet("SETTINGS")

settings.clear()

settings_data = pd.DataFrame({
    "SETTING": [
        "DEMA_PERIOD",
        "ATR_PERIOD",
        "SUPER_TREND_PERIOD",
        "SUPER_TREND_MULT",
        "RSI_PERIOD",
        "CONVICTION_THRESHOLD"
    ],
    "VALUE": [
        7,
        14,
        7,
        3,
        14,
        65
    ]
})

set_with_dataframe(
    settings,
    settings_data
)

print("SETTINGS UPDATED")

print("SYSTEM READY")
