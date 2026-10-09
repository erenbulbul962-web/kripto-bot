# MİDAS / Yahoo Kripto 15m EMA 50 Temas Botu (Gelişmiş Hata Yakalama)
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
TEMAS_TOL = 0.08                    # %8 Tolerans

# Yahoo Finance için alternatifli sembol sözlüğü
CRYPTO_SYMBOLS = {
    "BTC": ["BTC-USD"],
    "ETHFI": ["ETHFI-USD"],
    "BIO": ["BIO-USD", "BIO29983-USD"],
    "ENA": ["ENA-USD", "ENA19304-USD"],
    "FIL": ["FIL-USD"],
    "HOME": ["HOME-USD", "HOME1-USD"]
}

def main():
    print("--- TARAMA BAŞLADI ---")
    
    try:
        usdtry_df = yf.download("USDTRY=X", period="5d", interval="1d", progress=False)
        if isinstance(usdtry_df.columns, pd.MultiIndex):
            usdtry_df.columns = usdtry_df.columns.get_level_values(0)
        dolar_kur = float(usdtry_df["Close"].iloc[-1])
    except:
        dolar_kur = 34.0

    for coin, tickers in CRYPTO_SYMBOLS.items():
        df = None
        basarili_ticker = ""
        
        # Her coin için tanımlı ticker'ları sırayla dene (Biri olmazsa diğeri çalışır)
        for ticker in tickers:
            try:
                temp_df = yf.download(ticker, period=PERIYOT, interval="15m", progress=False)
                if isinstance(temp_df.columns, pd.MultiIndex):
                    temp_df.columns = temp_df.columns.get_level_values(0)
                temp_df = temp_df.dropna()
                
                if len(temp_df) >= MIN_MUM:
                    df = temp_df
                    basarili_ticker = ticker
                    break
            except:
                continue

        if df is None:
            print(f"{coin}: Hiçbir ticker ile veri alınamadı!")
            continue

        try:
            l, c = df["Low"].values, df["Close"].values
            ema = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean().values

            son_fiyat_tl = c[-1] * dolar_kur
            print(f"{coin} ({basarili_ticker}) -> Fiyat (TL): {son_fiyat_tl:.2f}")

            # Son 3 mum içinde temas kontrolü
            temas_var = False
            for i in [-1, -2, -3]:
                if l[i] <= ema[i] * (1 + TEMAS_TOL):
                    temas_var = True
                    break
            
            if temas_var:
                print(f"-> {coin} İÇİN TEMAS YAKALANDI! Bildirim gönderiliyor...")
                mesaj = f"🚨 EMA 50 TEMAS ALARMI!\nCoin: {coin}TRY\nFiyat: {round(son_fiyat_tl, 2)} TL\nDurum: EMA 50 Değdi/Yaklaştı!"
                telegram_bildirim_gonder(mesaj)
            else:
                print(f"-> {coin} için temas yok.")

        except Exception as e:
            print(f"HATA İŞLEME ({coin}): {e}")
            
    print("--- TARAMA BİTTİ ---")

if __name__ == "__main__":
    main()
