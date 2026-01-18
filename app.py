# =============================
# app.py
# =============================
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

GRAM_IN_OUNCE = 31.1035


def fetch_stock_gold_ratio(ticker: str, start_date: str) -> pd.DataFrame:
    stock = yf.download(
        ticker,
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    gold_ons = yf.download(
        "GC=F",
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    usdtry = yf.download(
        "USDTRY=X",
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if stock.empty or gold_ons.empty or usdtry.empty:
        raise RuntimeError("Finance data could not be fetched")

    stock_close = stock.xs("Close", level=0, axis=1).iloc[:, 0]
    gold_close = gold_ons.xs("Close", level=0, axis=1).iloc[:, 0]
    usdtry_close = usdtry.xs("Close", level=0, axis=1).iloc[:, 0]

    df = pd.concat(
        [
            stock_close.rename("stock_tl"),
            gold_close.rename("gold_ounce_usd"),
            usdtry_close.rename("usd_try"),
        ],
        axis=1,
    ).dropna()

    df["gold_gram_tl"] = (df["gold_ounce_usd"] * df["usd_try"]) / GRAM_IN_OUNCE
    df["stock_in_gram_gold"] = df["stock_tl"] / df["gold_gram_tl"]

    return df[["stock_in_gram_gold"]]



def fetch_crypto_gold_ratio(ticker: str, start_date: str) -> pd.DataFrame:
    stock = yf.download(
        ticker,
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    gold_ons = yf.download(
        "GC=F",
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if stock.empty or gold_ons.empty:
        raise RuntimeError("Finance data could not be fetched")

    stock_close = stock.xs("Close", level=0, axis=1).iloc[:, 0]
    gold_close = gold_ons.xs("Close", level=0, axis=1).iloc[:, 0]

    df = pd.concat(
        [
            stock_close.rename("crypto_usd"),
            gold_close.rename("gold_ounce_usd"),
        ],
        axis=1,
    ).dropna()

    df["gold_gram"] = df["gold_ounce_usd"] / GRAM_IN_OUNCE
    df["crypto_in_gram_gold"] = df["crypto_usd"] / df["gold_gram"]

    return df[["crypto_in_gram_gold"]]

@app.route("/api/stock/gold", methods=["GET"])
def stock_gold():
    start_date = request.args.get("start_date")
    ticker = request.args.get("ticker")

    if not start_date or not ticker:
        return jsonify({"error": "start_date and ticker are required"}), 400

    try:
        df = fetch_stock_gold_ratio(ticker, start_date)

        response = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "value": round(row.stock_in_gram_gold, 6),
            }
            for idx, row in df.iterrows()
        ]

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/crypto/gold", methods=["GET"])
def crypto_gold():
    start_date = request.args.get("start_date")
    ticker = request.args.get("ticker")

    if not start_date or not ticker:
        return jsonify({"error": "start_date and ticker are required"}), 400

    try:
        df = fetch_crypto_gold_ratio(ticker, start_date)

        response = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "value": round(row.crypto_in_gram_gold, 6),
            }
            for idx, row in df.iterrows()
        ]

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500