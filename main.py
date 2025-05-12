import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# URLs ของงบการเงิน
urls = {
    'Income Statement': 'https://stockanalysis.com/quote/bkk/{ticker}/financials/',
    'Balance Sheet Statement': 'https://stockanalysis.com/quote/bkk/{ticker}/financials/balance-sheet/',
    'Cash Flow Statement': 'https://stockanalysis.com/quote/bkk/{ticker}/financials/cash-flow-statement/',
}

# headers สำหรับ requests
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

def fetch_financial_data(ticker: str):
    result = {}

    for statement_type, url in urls.items():
        try:
            response = requests.get(url.format(ticker=ticker), headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = pd.read_html(str(soup), attrs={'data-test': 'financials'})

            if not tables:
                result[statement_type] = []
                continue

            df = tables[0]

            # จัดการ MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(col).strip() for col in df.columns.values]

            df = df.iloc[:, :-1]  # ลบคอลัมน์รวม
            df.columns.values[0] = 'item'

            df_long = df.melt(id_vars='item', var_name='date', value_name='value')

            df_long['period'] = df_long['date'].str.extract(r'^(TTM|FY|Q[1-4])')
            df_long['date'] = df_long['date'].str.extract(r'([A-Za-z]{3} \d{1,2}, \d{4})')
            df_long['date'] = pd.to_datetime(df_long['date'], errors='coerce')

            date_index = df_long.columns.get_loc('date')
            period_col = df_long.pop('period')
            df_long.insert(date_index, 'period', period_col)

            df_long['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_long.insert(0, 'symbol', ticker.upper())

            df_long['item'] = df_long['item'].str.strip().str.lower()
            df_long['value'] = (
                df_long['value']
                .astype(str)
                .str.replace(',', '', regex=False)
                .str.replace('%', '', regex=False)
                .str.replace('—', '', regex=False)
                .str.replace('N/A', '', regex=False)
                .str.replace('nan', '', regex=False)
                .str.strip()
            )
            df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
            df_long = df_long.dropna(subset=['date', 'value'])
            df_long = df_long.drop_duplicates()

            #  แปลงวันที่ให้อยู่ในรูปแบบ string (JSON-compatible)
            df_long['date'] = df_long['date'].dt.strftime('%Y-%m-%d')

            result[statement_type] = df_long.to_dict(orient='records')

        except Exception as e:
            result[statement_type] = {"error": f"An error occurred: {str(e)}"}

    return result

@app.get("/symbol={symbol}/income/")
def get_income_statement(symbol: str):
    return JSONResponse(content={"Income Statement": fetch_financial_data(symbol).get("Income Statement", [])})

@app.get("/symbol={symbol}/cashflow/")
def get_cashflow(symbol: str):
    return JSONResponse(content={"Cash Flow Statement": fetch_financial_data(symbol).get("Cash Flow Statement", [])})

@app.get("/symbol={symbol}/balancesheet/")
def get_balance_sheet(symbol: str):
    return JSONResponse(content={"Balance Sheet Statement": fetch_financial_data(symbol).get("Balance Sheet Statement", [])})
