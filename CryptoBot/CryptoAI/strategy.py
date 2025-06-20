def detect_dump_and_bounce(candles, threshold=-0.05, min_volume=100):
    """
    Улучшенная стратегия с проверкой объема и подтверждением
    Возвращает: (should_enter, entry_price, change_percent)
    """
    if len(candles) < 5:
        return False, 0, 0

    try:
        # Берем последние 3 свечи для анализа
        prev2 = candles[-3]
        prev1 = candles[-2]
        current = candles[-1]

        prev2_close = float(prev2[3])
        prev1_close = float(prev1[3])
        current_close = float(current[3])
        current_volume = float(current[4])

        # Расчет изменений
        prev_change = ((prev1_close - prev2_close) / prev2_close) * 100
        current_change = ((current_close - prev1_close) / prev1_close) * 100

        # Условия входа
        if (current_change <= threshold and
                current_volume > min_volume and
                abs(prev_change) < 0.3 and  # Фильтр боковика
                current_close < float(current[1]) and  # Закрытие ниже open
                (float(current[1]) - float(current[2])) / float(current[1]) > 0.1):  # Фильтр длинных верхних теней

            return True, current_close, current_change

    except Exception as e:
        print(f"Ошибка в стратегии: {str(e)}")

    return False, 0, 0