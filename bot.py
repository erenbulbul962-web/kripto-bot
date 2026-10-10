# MİDAS / Yahoo Kripto 15m EMA 50 Formasyon ve Grafik Botu
import matplotlib
matplotlib.use('Agg') # GitHub Actions sunucu hatasını önlemek için şarttır

import numpy as np
import pandas as pd
import yfinance as yf
import requests
import json
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# ================= TELEGRAM AYARLARI =================
TELEGRAM_TOKEN = "8439366459:AAHg5TB_CrHgRjNkex8IfzAkKQgUkE1toNQ"
TELEGRAM_CHAT_ID = "8571884020"
STATE_FILE = "last_alerted.json"

def telegram_bildirim_gonder(mesaj, resim_verisi=None):
    if resim_verisi:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('graph.png', resim_verisi)}
        payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": mesaj, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, files=files)
        except Exception as e:
            print("Telegram görseli gönderilemedi:", e)
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print("Telegram mesajı gönderilemedi:", e)

# ================= LİSTE TANIMLARI =================
CRYPTO_MAP = {
    "HOMETRY": ["HOME-USD", "HOME-TRY"],
    "ETHFITRY": ["ETHFI-USD", "ETHFI-TRY"],
    "BIOTRY": ["BIO-USD", "BIO-TRY"],
    "ENATRY": ["ENA-USD", "ENA-TRY"],
    "FILTRY": ["FIL-USD", "FIL-TRY"],
    "BTCTRY": ["BTC-USD", "BTC-TRY"],
    "FILUSDT": ["FIL-USD"],
    "KAIAUSDC": ["KAIA-USD"],
    "MANATRY": ["MANA-USD", "MANA-TRY"],
    "XLMNTRY": ["XLM-USD", "XLM-TRY"],
    "TREETRY": ["TREE-USD", "TREE-TRY"]
}

PERIYOT = "30d"
MIN_MUM = 60
EMA_PERIYOT = 50
TEMAS_TOL = 0.02  # %2 Hassas temas toleransı
GRAFIK_MUM_SAYISI = 30  # Grafikte gösterilecek son mum sayısı

def formasyon_analizi(df, i):
    open_p = df["Open"].iloc[i]
    close_p = df["Close"].iloc[i]
    high_p = df["High"].iloc[i]
    low_p = df["Low"].iloc[i]
    
    govde = abs(close_p - open_p)
    tum_boy = high_p - low_p
    if tum_boy == 0:
        tum_boy = 0.0001
        
    alt_fitil = min(open_p, close_p) - low_p
    ust_fitil = high_p - max(open_p, close_p)
    
    is_hammer = (alt_fitil >= 2 * govde) and (ust_fitil < govde * 0.5) and (close_p >= open_p)
    
    is_engulfing = False
    if i > 0:
        prev_open = df["Open"].iloc[i-1]
        prev_close = df["Close"].iloc[i-1]
        prev_is_red = prev_close < prev_open
        curr_is_green = close_p > open_p
        is_engulfing = prev_is_red and curr_is_green and (close_p >= prev_open) and (open_p <= prev_close)

    formasyonlar = []
    if is_hammer:
        formasyonlar.append("hammer")
    if is_engulfing:
        formasyonlar.append("bullish_engulfing")
        
    return formasyonlar

def state_yukle():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def state_kaydet(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass

def grafik_olustur(df, ema_verisi, display_name):
    df_plot = df.tail(GRAFIK_MUM_SAYISI)
    ema_plot = ema_verisi.tail(GRAFIK_MUM_SAYISI)
    
    apd = mpf.make_addplot(ema_plot, color='blue', width=1.5, panel=0)
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, gridstyle=':', y_on_right=True)
    
    buf = BytesIO()
    mpf.plot(df_plot, type='candle', style=s, addplot=apd, 
             title=f'\n{display_name} - 15m (EMA 50 Temas)', 
             ylabel='Fiyat', y_on_right=True,
             figscale=1.2, figsize=(10, 6),
             savefig=dict(fname=buf, dpi=100, bbox_inches='tight'))
    buf.seek(0)
    plt.close('all') # Bellek sızıntısını ve grafik pencerelerini temizle
    return buf

def main():
    last_states = state_yukle()
    new_states = last_states.copy()
    
    try:
        usdtry_df = yf.download("USDTRY=X", period="5d", interval="1d", progress=False)
        if isinstance(usdtry_df.columns, pd.MultiIndex):
            usdtry_df.columns = usdtry_df.columns.get_level_values(0)
        dolar_kur = float(usdtry_df["Close"].iloc[-1])
    except:
        dolar_kur = 34.0

    print("--- TARAMA BAŞLADI ---")
    for display_name, tickers in CRYPTO_MAP.items():
        df = None
        for ticker in tickers:
            try:
                temp_df = yf.download(ticker, period=PERIYOT, interval="15m", progress=False)
                if isinstance(temp_df.columns, pd.MultiIndex):
                    temp_df.columns = temp_df.columns.get_level_values(0)
                temp_df = temp_df.dropna()
                if len(temp_df) >= MIN_MUM:
                    df = temp_df
                    break
            except:
                continue
                
        if df is None or len(df) == 0:
            print(f"{display_name}: Veri alınamadı.")
            continue
            
        l = df["Low"].values
        c = df["Close"].values
        ema_serisi = df["Close"].ewm(span=EMA_PERIYOT, adjust=False).mean()
        ema = ema_serisi.values
        
        son_mum_zamani = str(df.index[-1])
        
        if last_states.get(display_name) == son_mum_zamani:
            continue
            
        i = -1
        if l[i] <= ema[i] * (1 + TEMAS_TOL):
            fiyat = c[i]
            if "TRY" in display_name and "USDT" not in display_name and "USDC" not in display_name:
                if not display_name.startswith("BTC") and not "TRY" in tickers[0]:
                    fiyat_goster = fiyat * dolar_kur
                else:
                    fiyat_goster = fiyat
            else:
                fiyat_goster = fiyat
                
            formasyonlar = formasyon_analizi(df, i)
            
            formasyon_metni = "Normal Temas"
            if "hammer" in formasyonlar and "bullish_engulfing" in formasyonlar:
                formasyon_metni = "Çekiç + Yutan Boğa (Güçlü Sinyal!)"
            elif "hammer" in formasyonlar:
                formasyon_metni = "Çekiç (Hammer)"
            elif "bullish_engulfing" in formasyonlar:
                formasyon_metni = "Yutan Boğa (Bullish Engulfing)"

            mesaj = (
                f"🚨 *EMA 50 TEMAS ALARMI!*\n\n"
                f"🪙 *Parite:* `{display_name}`\n"
                f"💰 *Fiyat:* `{fiyat_goster:.4f}`\n"
                f"📊 *Formasyon:* *{formasyon_metni}*\n"
                f"⏰ *Zaman:* `{son_mum_zamani}`"
            )
            
            print(f"-> {display_name} İÇİN TEMAS YAKALANDI! Grafik oluşturuluyor...")
            resim_buf = grafik_olustur(df, ema_serisi, display_name)
            telegram_bildirim_gonder(mesaj, resim_buf)
            
            new_states[display_name] = son_mum_zamani
        else:
            print(f"-> {display_name} için temas yok.")

    state_kaydet(new_states)
    print("--- TARAMA BİTTİ ---")

if __name__ == "__main__":
    main()
