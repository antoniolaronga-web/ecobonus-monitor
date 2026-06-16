import requests
import re
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SOGLIA = 11000

def get_plafond():
    url = "https://www.bonusveicolielettrici.mase.gov.it/veicolielettriciBeneficiario/api/numeri"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        # Il campo potrebbe chiamarsi "residuo" o simile
        residuo = data.get("residuo") or data.get("plafondResiduo") or data.get("disponibile")
        if residuo is not None:
            return float(residuo)
    except Exception:
        pass

    # Fallback: scraping HTML della pagina pubblica
    try:
        r = requests.get(
            "https://www.bonusveicolielettrici.mase.gov.it/veicolielettriciBeneficiario/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        match = re.search(r"residuo\s*[:\s]*([\d.,]+)\s*[€E]", r.text, re.IGNORECASE)
        if match:
            num = match.group(1).replace(".", "").replace(",", ".")
            return float(num)
    except Exception:
        pass

    return None

def send_telegram(residuo):
    msg = (
        f"🚨 *ECOBONUS DISPONIBILE\\!*\n\n"
        f"💰 Plafond residuo: *{residuo:,.0f} €*\n"
        f"🎯 Soglia superata: 11\\.000 €\n\n"
        f"👉 [Vai subito al portale](https://www.bonusveicolielettrici.mase.gov.it/veicolielettriciBeneficiario/#/plafond)\n\n"
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
        print(f"✅ Soglia superata! Invio notifica Telegram...")
        send_telegram(residuo)
    elif residuo is None:
        print("⚠️ Impossibile leggere il plafond.")
    else:
        print(f"⏳ Sotto soglia ({residuo} < {SOGLIA})")
