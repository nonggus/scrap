# %%
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time
import os
import pandas as pd

def get_cik_data():
    url = "https://www.sec.gov/files/company_tickers_exchange.json"
    headers = {'User-Agent': 'AgentIdea (Contact: chanathip.thc@gmail.com)'}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        fields = data.get('fields', [])
        cik_index = -1
        ticker_index = -1
        if 'cik' in fields:
            cik_index = fields.index('cik')
        elif 'cik_str' in fields:
            cik_index = fields.index('cik_str')
        if 'ticker' in fields:
            ticker_index = fields.index('ticker')

        company_data = data.get('data', [])
        cik_list = []
        ticker_list = []

        for item in company_data:
            cik = None
            ticker = None
            if cik_index != -1 and len(item) > cik_index:
                cik = str(item[cik_index]).zfill(10)
                cik_list.append(cik)
            if ticker_index != -1 and len(item) > ticker_index:
                ticker = item[ticker_index]
                ticker_list.append(ticker)
            else:
                ticker_list.append(None)

        df = pd.DataFrame({
            'cik_str': cik_list,
            'ticker': ticker_list,
        })
        return df

    except requests.exceptions.RequestException as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูล JSON: {e}")
        return None
    except Exception as e:
        print(f"เกิดข้อผิดพลาดโดยรวม: {e}")
        return None

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_experimental_option("prefs", {"download.prompt_for_download": False})

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def set_download_path(driver, path):
    params = {
        "behavior": "allow",
        "downloadPath": os.path.abspath(path)
    }
    driver.execute_cdp_cmd("Page.setDownloadBehavior", params)

def wait_for_download(path, timeout=30):
    """รอจนกว่าการดาวน์โหลดในโฟลเดอร์จะเสร็จสมบูรณ์"""
    seconds = 0
    while any(fname.endswith('.crdownload') for fname in os.listdir(path)):
        time.sleep(1)
        seconds += 1
        if seconds > timeout:
            print("⏳ การดาวน์โหลดใช้เวลานานเกินไป")
            break

def download_financial_statements(driver, ticker):
    base_url = "https://site.financialmodelingprep.com/financial-statements/"
    company_url = f"{base_url}{ticker}"

    output_folder = os.path.join("Financial", ticker)
    os.makedirs(output_folder, exist_ok=True)

    set_download_path(driver, output_folder)

    try:
        driver.get(company_url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]")))
        
        statements_to_download = ["Income Statement", "Cash Flow Statement", "Balance Sheet"]
        tab_index = 1

        for statement_name in statements_to_download:
            try:
                tab_xpath = f"/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]/button[{tab_index}]"
                tab_button = wait.until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
                tab_button.click()

                download_button_xpath = "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/button[2]"

                success = False
                for attempt in range(3):
                    try:
                        download_button = wait.until(EC.element_to_be_clickable((By.XPATH, download_button_xpath)))
                        download_button.click()
                        wait_for_download(output_folder)
                        print(f"✅ ดาวน์โหลด {statement_name} สำหรับ {ticker} เรียบร้อย")
                        success = True
                        break
                    except ElementClickInterceptedException:
                        print(f"⚠️ ปุ่ม {statement_name} ถูกบัง ลองใหม่ ({attempt+1}) ...")
                        time.sleep(1)

                if not success:
                    print(f"❌ ไม่สามารถดาวน์โหลด {statement_name} สำหรับ {ticker}")

            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการดาวน์โหลด {statement_name} สำหรับ {ticker}: {e}")

            tab_index += 1

    except Exception as e:
        print(f"เกิดข้อผิดพลาดกับ Ticker: {ticker} - {e}")

if __name__ == "__main__":
    cik_df = get_cik_data()
    if cik_df is not None:
        print("✅ ดึงข้อมูล CIK และ Ticker สำเร็จ\n")
        valid_symbols = set(cik_df['ticker'].dropna().str.upper())

        driver = setup_driver()

        try:
            while True:
                try:
                    symbol = input("\nกรอก Symbol (หรือพิมพ์ exit เพื่อออก): ").upper().strip()
                    if symbol == "EXIT":
                        print("👋 ออกจากโปรแกรม")
                        break

                    if not symbol:
                        print("⚠️ กรุณากรอก Symbol ให้ถูกต้อง")
                        continue

                    if symbol not in valid_symbols:
                        print("❌ Symbol ไม่ถูกต้อง หรือไม่พบในฐานข้อมูล กรุณาลองใหม่")
                        continue

                    print(f"▶️ กำลังดาวน์โหลดสำหรับ {symbol} ...")
                    download_financial_statements(driver, symbol)

                except KeyboardInterrupt:
                    print("\n🛑 รับสัญญาณหยุดจากผู้ใช้")
                    break

        finally:
            driver.quit()
            print("🛑 ปิด Browser แล้ว")


# %%