import requests
import pandas as pd
import json
import os
from datetime import datetime


def get_mexc_futures_klines(symbol="WIF_USDT", interval="Min1", limit=100):
    """
    Получение свечей с фьючерсного API MEXC с правильной обработкой формата данных

    Параметры:
    - symbol: BTC_USDT, ETH_USDT и др.
    - interval: Min1, Min5, Min15, Min30, Hour1, Hour4, Day1
    - limit: количество свечей (1-1000)
    """
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}"
    params = {
        "interval": interval,
        "limit": limit
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        print(f"Запрос к API MEXC: {url} с параметрами: {params}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", False):
            print(f"Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
            return None

        raw_data = data['data']

        # Проверка и адаптация к разным форматам ответа
        if 'vol' in raw_data:  # Если объем указан как 'vol'
            volume_key = 'vol'
        elif 'volume' in raw_data:  # Если объем указан как 'volume'
            volume_key = 'volume'
        else:
            print("⚠️ Не найден ключ для объема (vol/volume)")
            print("Полная структура ответа:")
            print(json.dumps(raw_data, indent=2))
            return None

        # Создаем DataFrame
        df = pd.DataFrame({
            'timestamp': raw_data['time'],
            'open': raw_data['open'],
            'high': raw_data['high'],
            'low': raw_data['low'],
            'close': raw_data['close'],
            'volume': raw_data[volume_key]
        })

        # Конвертируем timestamp в читаемые даты
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

        print(f"Успешно получено {len(df)} свечей")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {str(e)}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        return None

# Добавим возврат данных в том формате, который ожидает strategy.py
def get_klines(symbol="BTC_USDT", interval="Min1", limit=100):
    df = get_mexc_futures_klines(symbol, interval, limit)
    if df is not None:
        # Сохраняем свечи в CSV (добавляем новые данные)
        _save_candles_to_csv(df)
        return df[['open', 'high', 'low', 'close', 'volume']].values.tolist()
    return None


def _save_candles_to_csv(df):
    """Сохраняет свечи в CSV файл, обновляя существующие данные"""
    file_path = 'mexc_candles.csv'

    # Если файл существует, загружаем старые данные и объединяем
    if os.path.exists(file_path):
        old_df = pd.read_csv(file_path)
        df = pd.concat([old_df, df]).drop_duplicates('timestamp')

    # Сохраняем/перезаписываем файл
    df.to_csv(file_path, index=False)