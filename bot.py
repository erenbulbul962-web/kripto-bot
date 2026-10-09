# MİDAS TRY Kripto 15m EMA 50 Temas Botu
import numpy as np
import pandas as pd
import yfinance as yf
import requests
import warnings
warnings.filterwarnings('ignore')

# ================= TELEGRAM AYARLARI =================
TELEGRAM_TOKEN = "8439366459:AAHg5TB_CrHgRjNkex8IfzAkKQgUkE1toNQ"
TELEGRAM_CHAT_ID = "8571884020"

def telegram_bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram mesajı gönderilemedi:", e)

# ================= GENEL AYARLAR =================
PERIYOT = "60d"
MIN_MUM = 100
EMA_PERIYOT = 50
TEMAS_TOL = 0.03                    # %3 Tolerans

CRYPTO_LIST = [
    "BTC", "ETHFI", "BIO", "ENA", "FIL", "HOME"
]
CRYPTO_LIST = sorted(list(set(CRYPTO_LIST)))

def strateji_tara(df):
    df = df.dropna()
    n = len(df)
    if n < MIN_MUM:
        return None
    l, c = df["Low"].values, df["Close"].values
    ema = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean().values

    # Son 3 mum içinde Low değerinin EMA 50'ye %3 toleransla değip değmediğini kontrol eder
    temas_var = False
    for i in [-1, -2, -3]:
        if l[i] <= ema[i] * (1 + TEMAS_TOL):
            temas_var = True
            break
            
    if not temas_var:
        return None

    return {
        "Fiyat": round(c[-1], 2),
        "Durum": "EMA 50 Temas Etti!",
    }

def main():
    for coin in CRYPTO_LIST:
        s = coin + "-TRY"
        try:
            df = yf.download(s, period=PERIYOT, interval="15m", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            if len(df) < MIN_MUM:
                continue

            r = strateji_tara(df)
            if r:
                mesaj = f"🚨 EMA 50 TEMAS ALARMI!\nCoin: {coin}TRY\nFiyat: {r['Fiyat']}\nDurum: {r['Durum']}"
                telegram_bildirim_gonder(mesaj)
        except Exception:
            pass

if __name__ == "__main__":
    main()
