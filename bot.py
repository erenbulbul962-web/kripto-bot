# MİDAS TRY Kripto 15m Telegram Bildirimli Otomatik Tarama
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

# Sizin TradingView / Midas Listeniz (TRY Pariteleri)
CRYPTO_LIST = [
    "BTC", "ETHFI", "BIO", "ENA", "FIL", "HOME"
]
CRYPTO_LIST = sorted(list(set(CRYPTO_LIST)))

def strateji_tara(df):
    df = df.dropna()
    n = len(df)
    if n < MIN_MUM:
        return None
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    ema = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean().values

    temas_var = False
    for i in [-1, -2, -3]:
        if l[i] <= ema[i] * (1 + TEMAS_TOL):
            temas_var = True
            break
            
    if not temas_var:
        return None

    yesil_kapama = c[-1] > o[-1]
    alt_fitil = min(o[-1], c[-1]) - l[-1]
    govde = abs(c[-1] - o[-1])
    
    if not (yesil_kapama or (alt_fitil > govde * 0.5)):
        return None

    return {
        "Fiyat": round(c[-1], 2),
        "Durum": "EMA Teması + Tepki",
        "_s": c[-1] / ema[-1] - 1,
    }

def main():
    # Test amaçlı Telegram mesajı
    telegram_bildirim_gonder("🟢 Kripto 15m Botu aktif listenizle (TRY) taramaya başladı!")
    
    print(f"Tarama başlatıldı ({len(CRYPTO_LIST)} Midas coini taranıyor)...")
    sonuclar = []

    for coin in CRYPTO_LIST:
        s = coin + "-TRY"  # Midas TRY pariteleri için
        try:
            df = yf.download(s, period=PERIYOT, interval="15m", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            
            if len(df) < MIN_MUM:
                continue

            r = strateji_tara(df)
            if r:
                sonuclar.append(coin)
                mesaj = f"🚨 MİDAS TRY ALARMI!\nCoin: {coin}TRY\nFiyat: {r['Fiyat']}\nDurum: {r['Durum']}"
                telegram_bildirim_gonder(mesaj)
        except Exception:
            pass
            
    print(f"Tarama bitti. Eşleşen: {len(sonuclar)}")

if __name__ == "__main__":
    main()
