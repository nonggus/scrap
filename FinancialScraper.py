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

# *** ลบฟังก์ชัน get_cik_data() ออกไป ***
# def get_cik_data():
#     ... (ถูกลบออก) ...

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
    # Check for .crdownload files in the specified path
    while any(fname.endswith('.crdownload') for fname in os.listdir(path)):
        time.sleep(1)
        seconds += 1
        if seconds > timeout:
            print(f"⏳ การดาวน์โหลดใน {path} ใช้เวลานานเกินไป")
            break
    # Give a little extra time after .crdownload disappears for the file to finalize
    time.sleep(0.5)


def download_financial_statements(driver, ticker):
    base_url = "https://site.financialmodelingprep.com/financial-statements/"
    company_url = f"{base_url}{ticker}"

    try:
        print(f"กำลังเข้าถึงข้อมูลสำหรับ {ticker} บน FMP...")
        driver.get(company_url)

        # *** เพิ่มการตรวจสอบว่าหน้าโหลดสำเร็จและมี Element ที่คาดหวังหรือไม่ ***
        # รอ Element ที่บ่งชี้ว่าหน้าข้อมูลหุ้นนี้โหลดถูกต้อง
        wait = WebDriverWait(driver, 10) # ลดเวลารอลงนิดหน่อย ถ้า Symbol ผิดจะได้แจ้งเร็วขึ้น
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]")))
            print(f"✅ โหลดหน้าข้อมูล {ticker} สำเร็จบน FMP")
        except (TimeoutException, NoSuchElementException):
            # ถ้าหา Element สำคัญไม่เจอหลังจากรอ แสดงว่า Symbol นี้อาจไม่ถูกต้องบน FMP
            print(f"❌ ไม่พบข้อมูลสำหรับ Symbol '{ticker}' บน Financial Modeling Prep")
            print("โปรดตรวจสอบ Symbol และลองใหม่อีกครั้ง")
            return # ออกจากฟังก์ชันนี้ทันทีถ้าหาข้อมูลไม่เจอ


        statements_info = [
            ("Income Statement", 1, "Income Statement"),
            ("Cash Flow Statement", 2, "Cash Flow Statement"),
            ("Balance Sheet", 3, "Balance Sheet Statement")
        ]

        for statement_name, tab_index, folder_name in statements_info:
            # สร้างโฟลเดอร์ตามชื่อที่กำหนดโดยตรง
            statement_output_folder = folder_name
            os.makedirs(statement_output_folder, exist_ok=True)

            try:
                tab_xpath = f"/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/div[2]/button[{tab_index}]"
                tab_button = wait.until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
                tab_button.click()

                # หน่วงเวลาเพื่อให้เบราว์เซอร์ประมวลผลการเปลี่ยน Tab
                time.sleep(1)

                # ตั้งค่า download path หลังเปลี่ยน Tab และรอแล้ว
                set_download_path(driver, statement_output_folder)
                # เพิ่ม print เพื่อยืนยันว่าตั้งค่า path แล้ว
                print(f"✨ ตั้งค่าปลายทางการดาวน์โหลดสำหรับ {statement_name} ไปยังโฟลเดอร์ '{folder_name}'")


                # ค้นหาและคลิกปุ่มดาวน์โหลด (ตำแหน่งปุ่มดาวน์โหลดเหมือนเดิม)
                download_button_xpath = "/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div/div[1]/div/button[2]"

                success = False
                for attempt in range(3):
                    try:
                        download_button = wait.until(EC.element_to_be_clickable((By.XPATH, download_button_xpath)))
                        download_button.click()
                        # รอจนกว่าการดาวน์โหลดในโฟลเดอร์ที่กำหนดจะเสร็จ
                        wait_for_download(statement_output_folder)
                        print(f"✅ ดาวน์โหลด {statement_name} สำหรับ {ticker} ไปยังโฟลเดอร์ '{folder_name}' เรียบร้อย")
                        success = True
                        break
                    except ElementClickInterceptedException:
                        print(f"⚠️ ปุ่ม {statement_name} ถูกบัง ลองใหม่ ({attempt+1}) ...")
                        time.sleep(1)

                if not success:
                    print(f"❌ ไม่สามารถดาวน์โหลด {statement_name} สำหรับ {ticker}")

            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการดาวน์โหลด {statement_name} สำหรับ {ticker}: {e}")

    # *** ปรับปรุงข้อความ Error หลัก ***
    except Exception as e:
        print(f"⛔️ เกิดข้อผิดพลาดที่ไม่คาดคิดในการประมวลผล Ticker: {ticker} - {e}")
        print("อาจมีปัญหาในการเข้าถึงเว็บไซต์ หรือปัญหาอื่นๆ")


if __name__ == "__main__":
    # *** ลบการเรียกใช้ get_cik_data และการสร้าง valid_symbols ออกไป ***
    # cik_df = get_cik_data()
    # if cik_df is not None:
    #     print("✅ ดึงข้อมูล CIK และ Ticker สำเร็จ\n")
    #     valid_symbols = set(cik_df['ticker'].dropna().str.upper())

    driver = setup_driver()

    try:
        while True:
            try:
                # ข้อความแจ้งเตือนผู้ใช้
                symbol = input("\nกรุณากรอก Symbol หุ้น (เช่น AAPL, GOOG, RY): ").upper().strip() # ปรับข้อความให้กว้างขึ้น
                if symbol == "EXIT":
                    print("👋 ออกจากโปรแกรม")
                    break

                if not symbol:
                    print("⚠️ กรุณากรอก Symbol ให้ถูกต้อง")
                    continue

                # *** ลบการตรวจสอบ valid_symbols ออกไป ***
                # if symbol not in valid_symbols:
                #     print("❌ Symbol ไม่ถูกต้อง หรือไม่พบในฐานข้อมูล CIK ของ SEC กรุณาลองใหม่")
                #     continue

                print(f"▶️ กำลังดำเนินการสำหรับ {symbol} ...")
                # โปรแกรมจะพยายามดาวน์โหลดเลย และไปแจ้งข้อผิดพลาดในฟังก์ชัน download_financial_statements ถ้า Symbol ผิด
                download_financial_statements(driver, symbol)

            except KeyboardInterrupt:
                print("\n🛑 รับสัญญาณหยุดจากผู้ใช้")
                break

    finally:
        driver.quit()
        print("🛑 ปิด Browser แล้ว")

# %%