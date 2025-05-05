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
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
import time
import os
import pandas as pd

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
    seconds = 0
    while any(fname.endswith('.crdownload') for fname in os.listdir(path)):
        time.sleep(1)
        seconds += 1
        if seconds > timeout:
            print(f"⏳ Download in {path} is taking too long.")
            break
    time.sleep(0.5)

def download_financial_statements(driver, ticker):
    base_url = "https://site.financialmodelingprep.com/financial-statements/"
    company_url = f"{base_url}{ticker}"

    try:
        print(f"Accessing data for {ticker} on FMP...")
        driver.get(company_url)

        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]")))
            print(f"✅ Loaded {ticker} page successfully.")
        except (TimeoutException, NoSuchElementException):
            print(f"❌ No data found for symbol '{ticker}' on FMP.")
            return

        statements_info = [
            ("Income Statement", 1, "Income Statement"),
            ("Cash Flow Statement", 2, "Cash Flow Statement"),
            ("Balance Sheet", 3, "Balance Sheet Statement")
        ]

        for statement_name, tab_index, folder_name in statements_info:
            os.makedirs(folder_name, exist_ok=True)

            try:
                tab_xpath = f"/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]/button[{tab_index}]"
                tab_button = wait.until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
                tab_button.click()
                time.sleep(1)

                set_download_path(driver, folder_name)
                print(f"✨ Set download path for {statement_name} to '{folder_name}'")

                download_button_xpath = "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/button[2]"

                success = False
                for attempt in range(3):
                    try:
                        download_button = wait.until(EC.element_to_be_clickable((By.XPATH, download_button_xpath)))
                        download_button.click()
                        wait_for_download(folder_name)
                        print(f"✅ Downloaded {statement_name} for {ticker} to '{folder_name}'")
                        success = True
                        break
                    except ElementClickInterceptedException:
                        print(f"⚠️ {statement_name} button blocked. Retrying ({attempt + 1})...")
                        time.sleep(1)

                if not success:
                    print(f"❌ Failed to download {statement_name} for {ticker}")

            except Exception as e:
                print(f"⚠️ Error downloading {statement_name} for {ticker}: {e}")

    except Exception as e:
        print(f"⛔ Unexpected error while processing ticker {ticker}: {e}")

if __name__ == "__main__":
    driver = setup_driver()

    try:
        while True:
            try:
                symbol = input("\nEnter stock symbol (e.g., AAPL, GOOG, RY): ").upper().strip()
                if symbol == "EXIT":
                    print("👋 Exiting program.")
                    break

                if not symbol:
                    print("⚠️ Please enter a valid symbol.")
                    continue

                print(f"▶️ Processing {symbol}...")
                download_financial_statements(driver, symbol)

            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user.")
                break

    finally:
        driver.quit()
        print("🛑 Browser closed.")

# %%