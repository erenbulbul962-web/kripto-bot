# MİDAS TRY Kripto 15m EMA 50 Temas Botu (Log Kontrollü)
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
MIN_MUM = 30
EMA_PERIYOT = 50
TEMAS_TOL = 0.08                    # Kesin yakalamak için toleransı %8 yaptık

CRYPTO_SYMBOLS = {
    "BTC": "BTC-TRY",
    "ETHFI": "ETHFI-TRY",
    "BIO": "BIO-TRY",
    "ENA": "ENA-TRY",
    "FIL": "FIL-TRY",
    "HOME": "HOME-TRY"
}

def main():
    print("--- TARAMA BAŞLADI ---")
    for coin, ticker in CRYPTO_SYMBOLS.items():
        try:
            df = yf.download(ticker, period=PERIYOT, interval="15m", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            if len(df) < MIN_MUM:
                print(f"{coin}: Yetersiz veri ({len(df)} mum)")
                continue

            l, c = df["Low"].values, df["Close"].values
            ema = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean().values

            son_fiyat = c[-1]
            son_ema = ema[-1]
            print(f"{coin} -> Fiyat: {son_fiyat:.2f}, EMA50: {son_ema:.2f}, Low[-1]: {l[-1]:.2f}")

            # Son 3 mumda temas kontrolü
            temas_var = False
            for i in [-1, -2, -3]:
                if l[i] <= ema[i] * (1 + TEMAS_TOL):
                    temas_var = True
                    break
            
            if temas_var:
                print(f"-> {coin} İÇİN TEMAS YAKALANDI! Bildirim gönderiliyor...")
                mesaj = f"🚨 EMA 50 TEMAS ALARMI!\nCoin: {coin}TRY\nFiyat: {round(son_fiyat, 2)}\nDurum: EMA 50 Değdi/Yaklaştı!"
                telegram_bildirim_gonder(mesaj)
            else:
                print(f"-> {coin} için temas yok.")

        except Exception as e:
            print(f"HATA ({coin}): {e}")
    print("--- TARAMA BİTTİ ---")

if __name__ == "__main__":
    main()
