import pandas as pd
import numpy as np
import os
from scipy import stats
from datetime import datetime, timedelta, timezone

def detectOutliersIQR(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    if IQR == 0:
        return pd.Series([False] * len(series), index=series.index)
    return (series < (Q1 - 1.5 * IQR)) | (series > (Q3 + 1.5 * IQR))

def detectOutlierZ(series, threshold=3):
    if series.std() == 0:
        return pd.Series([False] * len(series), index=series.index)
    z_scores = np.abs(stats.zscore(series))
    return pd.Series(z_scores > threshold, index=series.index)

def isPriceOutlier(symbol: str, live_price: float) -> bool:
    symbol = symbol.upper()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'hist_data_backup'))
    file_path = os.path.join(base_dir, f"{symbol}.csv")

    if not os.path.exists(file_path):
        print(f"[Outlier] Historical data file not found for {symbol}")
        return False

    try:
        df = pd.read_csv(file_path)
        prices = pd.concat([
            df['open'].astype(float),
            df['close'].astype(float)
        ], ignore_index=True)
    except Exception as e:
        print(f"[Outlier] Failed to read or process data for {symbol}: {e}")
        return False

    # Append the live price to evaluate as a potential outlier
    combined_prices = pd.concat([prices, pd.Series([live_price])], ignore_index=True)

    iqr_flag = detectOutliersIQR(combined_prices).iloc[-1]
    z_flag = detectOutlierZ(combined_prices).iloc[-1]

    return bool(iqr_flag or z_flag)