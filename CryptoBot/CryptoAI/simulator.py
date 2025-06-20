import csv
import json
import os
from datetime import datetime


class TradeSimulator:
    def __init__(self, take_profit=0.8, stop_loss=0.5):
        self.position = None
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trade_history = []
        self.total_profit = 0
        self.total_loss = 0
        self._prepare_files()  # Инициализация файлов

    def _prepare_files(self):
        """Создает файлы для записи при первом запуске"""
        # Для истории сделок (CSV)
        if not os.path.exists('trade_history.csv'):
            with open('trade_history.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'entry_time', 'exit_time', 'entry_price',
                    'exit_price', 'result', 'pnl_percent', 'duration_sec'
                ])

        # Для статистики (JSON)
        if not os.path.exists('trade_stats.json'):
            with open('trade_stats.json', 'w') as f:
                json.dump({
                    "total_trades": 0,
                    "profit_trades": 0,
                    "total_profit": 0,
                    "total_loss": 0
                }, f)

    def enter_trade(self, entry_price, timestamp=None):
        self.position = {
            "entry": entry_price,
            "status": "open",
            "entry_time": timestamp or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "exit_time": None,
            "exit_price": None,
            "result": None,
            "pnl_percent": None,
            "duration_sec": None
        }
        print(f"✅ Вход по цене {entry_price}")

    def check_exit(self, current_price):
        if not self.position or self.position["status"] != "open":
            return None

        entry = self.position["entry"]
        change = ((current_price - entry) / entry) * 100

        if change >= self.take_profit:
            return self.close_position(current_price, "profit", f"+{change:.2f}%")
        elif change <= -self.stop_loss:
            return self.close_position(current_price, "loss", f"{change:.2f}%")
        return None

    def close_position(self, exit_price, result, change_str):
        now = datetime.utcnow()
        entry_time = datetime.strptime(self.position["entry_time"], '%Y-%m-%d %H:%M:%S')
        pnl_percent = float(change_str.strip('%'))

        # Обновляем статистику
        if result == "profit":
            self.total_profit += pnl_percent
        else:
            self.total_loss += abs(pnl_percent)

        self.position.update({
            "status": "closed",
            "exit_price": exit_price,
            "result": result,
            "exit_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            "pnl_percent": pnl_percent,
            "duration_sec": (now - entry_time).total_seconds()
        })

        self.trade_history.append(self.position.copy())
        self._save_trade_to_csv(self.position)
        self._update_stats()
        return self.position

    def _save_trade_to_csv(self, trade):
        """Добавляет сделку в CSV файл"""
        with open('trade_history.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                trade['entry_time'],
                trade['exit_time'],
                trade['entry'],
                trade['exit_price'],
                trade['result'],
                trade['pnl_percent'],
                trade['duration_sec']
            ])

    def _update_stats(self):
        """Обновляет статистику в JSON файле"""
        stats = {
            "total_trades": len(self.trade_history),
            "profit_trades": sum(1 for t in self.trade_history if t['result'] == 'profit'),
            "total_profit": self.total_profit,
            "total_loss": self.total_loss,
            "profit_factor": self.total_profit / self.total_loss if self.total_loss else float('inf')
        }

        with open('trade_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)

    def save_history(self):
        """Сохраняет полную историю сделок"""
        self._update_stats()
        with open('trade_history_full.json', 'w') as f:
            json.dump(self.trade_history, f, indent=2)
        print("Данные успешно сохранены")