import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

# โฟลเดอร์หลัก
base_folder = 'Financial Statements'

# กำหนด header สำหรับ request
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# URL สำหรับงบการเงินแต่ละประเภท
urls = {
    'Income': 'https://stockanalysis.com/stocks/{ticker}/financials/',
    'Balance Sheet': 'https://stockanalysis.com/stocks/{ticker}/financials/balance-sheet/',
    'Cash Flow': 'https://stockanalysis.com/stocks/{ticker}/financials/cash-flow-statement/',
    'Ratio': 'https://stockanalysis.com/stocks/{ticker}/financials/ratios/',
}

while True:
    ticker = input("Enter the stock ticker symbol (e.g., AAPL, TSLA) or type 'exit' to quit: ").strip().lower()
    
    if ticker == 'exit':
        print("Exiting...")
        break
    
    if not ticker:
        print("❌ Ticker symbol cannot be empty. Please enter a valid ticker.")
        continue

    valid_ticker = False
    for statement_type, url in urls.items():
        print(f"Scraping {statement_type} for {ticker.upper()}...")

        response = requests.get(url.format(ticker=ticker), headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Invalid ticker symbol '{ticker.upper()}'. Please try again.")
            valid_ticker = False
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = pd.read_html(str(soup), attrs={'data-test': 'financials'})

        if not tables:
            print(f"❌ No data found for {statement_type}. The ticker might be incorrect.")
            valid_ticker = False
            break
        
        valid_ticker = True

    if valid_ticker:
        for statement_type, url in urls.items():
            print(f"Scraping {statement_type} for {ticker.upper()}...")

            response = requests.get(url.format(ticker=ticker), headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = pd.read_html(str(soup), attrs={'data-test': 'financials'})

            df = tables[0]

            # จัดการ MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(col).strip() for col in df.columns.values]

            # ตัดคอลัมน์สุดท้าย
            df = df.iloc[:, :-1]

            # เปลี่ยนชื่อคอลัมน์แรก
            df.columns.values[0] = 'Item'

            # แปลง Wide → Long format
            id_col = df.columns[0]
            df_long = df.melt(id_vars=id_col, var_name='Date', value_name='Value')

            # แปลง Date ให้เป็น datetime
            df_long['Date'] = df_long['Date'].str.extract(r'([A-Za-z]{3} \d{1,2}, \d{4})')
            df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')

             # เพิ่มคอลัมน์ created_at
            df_long.insert(0, 'Symbol', ticker.upper())
            df_long['Created_at'] = datetime.now()
            
            # Data Cleaning
            df_long['Item'] = df_long['Item'].str.strip()
            df_long['Value'] = (
                df_long['Value']
                .astype(str)
                .str.replace(',', '', regex=False)
                .str.replace('%', '', regex=False)
                .str.replace('—', '', regex=False)
                .str.replace('N/A', '', regex=False)
                .str.replace('nan', '', regex=False)
                .str.strip()
            )
            df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
            df_long = df_long.dropna(subset=['Date', 'Value'])
            df_long = df_long.drop_duplicates()


            # สร้างโฟลเดอร์สำหรับเก็บไฟล์
            folder_path = os.path.join(base_folder, statement_type)
            os.makedirs(folder_path, exist_ok=True)

            # ตั้งชื่อไฟล์ CSV
            file_name = f"{ticker.upper()}-{statement_type}.csv"
            file_path = os.path.join(folder_path, file_name)

            # บันทึกเป็น CSV
            df_long.to_csv(file_path, index=False)
            print(f"✅ Saved to {file_path}")

        print("🎉 Done!\n")
