name: Kripto 15m Bot

on:
  schedule:
    - cron: '*/5 * * * *'  # Her 5 dakikada bir çalışır
  workflow_dispatch:      # Manuel tetikleme imkanı

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Kodları Çek
        uses: actions/checkout@v3

      - name: Python Kur
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Kütüphaneleri Yükle
        run: |
          python -m pip install --upgrade pip
          pip install pandas numpy requests yfinance mplfinance matplotlib

      - name: Botu Çalıştır
        run: python bot.py
