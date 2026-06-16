import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        time.sleep(8)  # attendi rendering Angular

        # Stampa tutto il testo visibile
        testo = driver.find_element(By.TAG_NAME, "body").text
        print("=== TESTO PAGINA (primi 1000 char) ===")
        print(testo[:1000])
        print("=== FINE TESTO ===")

        # Stampa anche il source HTML per vedere i dati grezzi
        html = driver.page_source
        print("=== HTML (primi 2000 char) ===")
        print(html[:2000])
        print("=== FINE HTML ===")

        # Cerca "residuo" nel testo
        match = re.search(r"residuo\s+([\d.,]+)\s*€", testo, re.IGNORECASE)
        if match:
            num = match.group(1).replace(".", "").replace(",", ".")
            return float(num)

        # Cerca anche nell'HTML
        match2 = re.search(r"residuo[^€]*?([\d.,]+)\s*€", html, re.IGNORECASE)
        if match2:
            num = match2.group(1).replace(".", "").replace(",", ".")
            return float(num)

    except Exception as e:
        print(f"Errore: {e}")
    finally:
        driver.quit()
    return None

def send_telegram(residuo):
    msg = (
        f"🚨 *ECOBONUS DISPONIBILE\\!*\n\n"
        f"💰 Plafond residuo: *{residuo:,.0f} €*\n"
        f"🎯 Soglia superata: 11\\.000 €\n\n"
        f"👉 [Vai subito al portale]({URL})\n\n"
        f"⏰ Hai 30 giorni per usare il voucher\\!"
    )
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False
        },
        timeout=10
    )

if __name__ == "__main__":
    residuo = get_plafond()
    print(f"Plafond residuo rilevato: {residuo}")
    if residuo is not None and residuo >= SOGLIA:
        print("✅ Soglia superata! Invio notifica Telegram...")
        send_telegram(residuo)
    elif residuo is None:
        print("⚠️ Impossibile leggere il plafond.")
    else:
        print(f"⏳ Sotto soglia ({residuo} < {SOGLIA})")
        send_telegram(residuo)
