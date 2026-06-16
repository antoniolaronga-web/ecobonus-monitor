import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.by import By

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SOGLIA = 11000
URL = "https://www.bonusveicolielettrici.mase.gov.it/veicolielettriciBeneficiario/#/plafond"

def get_plafond():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL)
        time.sleep(8)
        testo = driver.find_element(By.TAG_NAME, "body").text
        print("=== TESTO PAGINA ===")
        print(testo[:1000])
        print("=== FINE ===")

        match = re.search(r"residuo\s+([\d.,]+)\s*€", testo, re.IGNORECASE)
        if match:
            num = match.group(1).replace(".", "").replace(",", ".")
            return float(num)
    except Exception as e:
        print(f"Errore Selenium: {e}")
    finally:
        driver.quit()
    return None

def send_telegram(testo):
    print(f"Invio Telegram a chat_id={CHAT_ID}...")
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": testo,
        },
        timeout=10
    )
    print(f"Risposta Telegram: {r.status_code} - {r.text}")

if __name__ == "__main__":
    # Test immediato Telegram
    send_telegram("🔔 Test Ecobonus Monitor - funziona!")

    residuo = get_plafond()
    print(f"Plafond residuo rilevato: {residuo}")

    if residuo is not None and residuo >= SOGLIA:
        send_telegram(f"🚨 ECOBONUS DISPONIBILE! Residuo: {residuo:,.0f} € - Vai su: {URL}")
    elif residuo is None:
        send_telegram("⚠️ Ecobonus Monitor: impossibile leggere il plafond.")
    else:
        send_telegram(f"⏳ Ecobonus: plafond sotto soglia. Residuo attuale: {residuo:,.0f} €")
