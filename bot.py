# MİDAS TRY Kripto 15m EMA 50 Temas Botu (Hata Ayıklamalı)
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
MIN_MUM = 50
EMA_PERIYOT = 50
TEMAS_TOL = 0.05                    # Toleransı %5'e esnettik (Gözden kaçmasın diye)

# Yahoo Finance uyumlu TRY parite formatı
CRYPTO_SYMBOLS = {
    "BTC": "BTC-TRY",
    "ETHFI": "ETHFI-TRY",
    "BIO": "BIO29983-TRY", # Yahoo'daki güncel listeleme adına göre gerekirse güncellenir
    "ENA": "ENA19304-TRY",
    "FIL": "FIL-TRY",
    "HOME": "HOME-TRY"
}

def strateji_tara(df):
    df = df.dropna()
    n = len(df)
    if n < MIN_MUM:
        return None
    l, c = df["Low"].values, df["Close"].values
    ema = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean().values

    # Son 3 mum içinde Low değerinin EMA 50'ye teması
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
    for coin, ticker in CRYPTO_SYMBOLS.items():
        try:
            df = yf.download(ticker, period=PERIYOT, interval="15m", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            if len(df) < MIN_MUM:
                print(f"{coin}: Yetersiz veri ({len(df)} mum)")
                continue

            r = strateji_tara(df)
            if r:
                mesaj = f"🚨 EMA 50 TEMAS ALARMI!\nCoin: {coin}TRY\nFiyat: {r['Fiyat']}\nDurum: {r['Durum']}"
                telegram_bildirim_gonder(mesaj)
                print(f"ALARM GÖNDERİLDİ: {coin}")
        except Exception as e:
            print(f"Hata ({coin}): {e}")

if __name__ == "__main__":
    main()
