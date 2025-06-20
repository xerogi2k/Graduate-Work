import time
import logging
from datetime import datetime
from mexc_api import get_klines
from strategy import detect_dump_and_bounce
from simulator import TradeSimulator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()


def main():
    sim = TradeSimulator(take_profit=0.8, stop_loss=0.5)
    logger.info("Торговый бот запущен")

    try:
        while True:
            try:
                # Получаем свечи
                candles = get_klines("WIF_USDT", interval="Min1", limit=100)

                if not candles or len(candles) < 10:
                    logger.warning("Недостаточно данных, ожидание...")
                    time.sleep(30)
                    continue

                last_price = float(candles[-1][3])
                logger.info(f"Текущая цена: {last_price:.4f}")

                # Проверяем стратегию
                should_enter, entry_price, change = detect_dump_and_bounce(candles)

                # Логика входа
                if should_enter and not sim.position:
                    logger.info(f"Сигнал на вход! Цена: {entry_price:.2f}, Изменение: {change:.2f}%")
                    sim.enter_trade(entry_price, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

                # Логика выхода
                if sim.position and sim.position["status"] == "open":
                    result = sim.check_exit(last_price)
                    if result:
                        logger.info(f"Сделка закрыта: {result['result']} ({result['pnl_percent']:.2f}%)")

                time.sleep(10)

            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {str(e)}")
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Остановка бота...")
        sim.save_history()
        logger.info("Бот успешно остановлен")


if __name__ == "__main__":
    main()