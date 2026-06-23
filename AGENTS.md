# AGENTS.md - AutoTrading / VКR Context

Этот файл нужен, чтобы в следующих сессиях быстро восстановить контекст проекта и диплома.

## Роль ассистента

Ты помогаешь как:

- технический консультант по проекту;
- reviewer кода;
- научный консультант по ВКР;
- помощник по формулировкам для диплома и защиты.

Главное правило: **опирайся только на реально реализованный проект**. Не придумывай функциональность, которой нет в коде. Если факт не подтверждён, сначала проверь код.

## Тема ВКР

Тема: **«Фьючерсная торговля криптовалютой с использованием AI/ML»**.

По смыслу это диплом по программной инженерии, а не работа по трейдингу. Основной акцент:

- микросервисная архитектура;
- обработка рыночных данных;
- ML pipeline;
- backtesting;
- walk-forward validation;
- dashboard для анализа результатов;
- воспроизводимость экспериментов.

Предметная область торговли используется как прикладной контекст.

## Назначение проекта

Проект представляет собой микросервисную систему для исследования ML-стратегий фьючерсной торговли криптовалютой.

Система предназначена для:

- получения исторических рыночных данных;
- формирования признаков;
- обучения модели XGBoost;
- генерации вероятностного прогноза;
- преобразования вероятности в торговый сигнал;
- расчёта параметров риска;
- исторического тестирования;
- walk-forward проверки;
- визуализации результатов в dashboard.

Система **не является полноценным ботом реальной торговли**. Основной контур - исследовательский.

## Рабочая директория

```text
/Users/xerogi/Documents/AutoTrading
```

## Основные сервисы

### Market Data Service

Папка:

```text
services/market-data-service
```

Назначение:

- обращается к BingX API;
- получает свечи;
- приводит данные к OHLCV-формату;
- сохраняет свечи в PostgreSQL;
- возвращает свечи dashboard/API-клиенту.

Формат свечи:

```text
timestamp
open
high
low
close
volume
```

Важно: Market Data Service не обучает модель и не принимает торговые решения.

### ML Service

Папка:

```text
services/ml-service
```

Назначение:

- получает OHLCV-данные;
- сортирует данные по времени;
- рассчитывает признаки;
- формирует target;
- делает train/test или walk-forward split;
- обучает XGBoost;
- возвращает probability и prediction.

Ключевые файлы:

```text
services/ml-service/features/dataset.py
services/ml-service/features/indicators.py
services/ml-service/features/advanced.py
services/ml-service/app/services/training.py
services/ml-service/app/ml/xgboost_model.py
```

ML pipeline:

```text
OHLCV -> features -> target -> split -> XGBoost -> probability -> prediction
```

### Strategy Service

Папка:

```text
services/strategy-service
```

Назначение:

- принимает probability от ML Service;
- сравнивает probability с entry threshold;
- применяет trend filter;
- формирует торговый сигнал: BUY / SELL / HOLD.

Основная конфигурация для диплома использует `long_only / soft`, поэтому основной рабочий сценарий - BUY или HOLD.

### Risk Manager

Папка:

```text
services/risk-manager
```

Назначение:

- рассчитывает параметры риск-менеджмента;
- stop-loss;
- take-profit;
- размер позиции/риск.

Основная логика:

```text
SL distance = ATR * ATR multiplier
TP distance = SL distance * RR
```

Для long:

```text
SL = entry_price - ATR * multiplier
TP = entry_price + (ATR * multiplier * RR)
```

### Backtesting Service

Папка:

```text
services/backtesting-service
```

Назначение:

- симулирует сделки на исторических данных;
- открывает позицию на следующей свече после сигнала;
- учитывает stop-loss, take-profit, time_exit;
- считает PnL, winrate, profit factor, max drawdown, equity curve.

Важный подтверждённый факт:

- backtest не входит на той же свече;
- сигнал сначала становится `pending_signal`;
- вход происходит на `open` следующей свечи;
- это покрыто тестом `test_signal_enters_on_next_candle_open`.

### Dashboard

Папка:

```text
dashboard
```

Реализован на Streamlit.

Назначение:

- выбор параметров;
- запуск walk-forward;
- отображение торговых метрик;
- отображение ML-метрик;
- equity curve;
- drawdown curve;
- таблица сделок;
- walk-forward windows;
- demo mode для защиты/видео.

Demo mode:

- включён по умолчанию;
- скрывает Advanced / Research;
- показывает основные вкладки: Обзор, Walk-forward, Сделки, Модель, Сервисы;
- использует дефолты основной 4h-конфигурации.

### Execution Service

Папка:

```text
services/execution-service
```

Назначение:

- вспомогательный сервис для paper trading;
- создаёт виртуальные сделки;
- закрывает виртуальные сделки;
- сохраняет paper-сделки в PostgreSQL;
- позволяет получить список paper-сделок через API.

Endpoints:

```text
POST /paper/orders
POST /paper/close
GET  /paper/trades
```

Важно:

- Execution Service не участвует в основном контуре backtesting/walk-forward;
- dashboard сейчас не выводит paper trades из Execution Service;
- это задел для будущего перехода от исторического тестирования к paper/live trading;
- в дипломе не преувеличивать его роль.

Корректная формулировка:

> Execution Service реализует базовый контур paper trading. В текущей версии он не участвует в расчёте исторических результатов и используется как вспомогательный компонент для сохранения виртуальных сделок в PostgreSQL.

## PostgreSQL

В проекте используется PostgreSQL.

Что хранится:

- рыночные свечи;
- paper trades для Execution Service.

Что НЕ хранится:

- история backtesting запусков;
- история walk-forward запусков;
- equity curve по каждому эксперименту;
- полные таблицы сделок backtest;
- grid-search результаты как отдельная история экспериментов.

Корректная формулировка:

> PostgreSQL используется для хранения прикладных данных системы, включая рыночные свечи и виртуальные сделки paper trading. Результаты backtesting и walk-forward testing в текущей реализации рассчитываются по запросу и отображаются в dashboard, но не сохраняются как отдельная история экспериментов.

## FastAPI

Серверные сервисы реализованы на FastAPI.

К ним относятся:

- market-data-service;
- ml-service;
- strategy-service;
- risk-manager;
- backtesting-service;
- execution-service.

Dashboard реализован отдельно на Streamlit.

## ML-модель

Используется XGBoost для бинарной классификации.

Модель получает не “сырые свечи” напрямую в человеческом смысле, а матрицу признаков, рассчитанную на основе OHLCV.

Цикл:

```text
OHLCV candles
-> feature engineering
-> X matrix
-> target vector y
-> XGBoost training
-> probability(target=1)
-> entry threshold
-> signal candidate
```

### Входные данные

Исходные данные:

```text
timestamp
open
high
low
close
volume
```

### Признаки

Базовые и расширенные признаки включают:

- OHLCV values;
- RSI;
- MACD;
- EMA 20;
- EMA 50;
- ATR;
- rolling volatility;
- trend_strength;
- trend_direction_score;
- trend_direction;
- market_regime;
- regime_trend;
- regime_range;
- regime_high_volatility;
- multi-timeframe признаки.

### Target

Есть два режима:

```text
future_return
barrier
```

В dashboard/основном исследовании чаще используется `barrier`.

Для `future_return`:

```text
future_return = Close[t + horizon] / Close[t] - 1
target = 1, если future_return > threshold
```

Для `barrier` long:

```text
take_profit_price = Close[t] * (1 + threshold)
stop_loss_price = Close[t] * (1 - stop_loss_threshold)
target = 1, если take-profit достигнут раньше stop-loss в пределах horizon
target = 0 иначе
```

### XGBoost score

XGBoost строит ансамбль деревьев.

Итоговый score:

```text
score(x) = base_score + tree_1(x) + tree_2(x) + ... + tree_K(x)
```

Вероятность:

```text
probability = 1 / (1 + exp(-score))
```

Вес листа дерева во время обучения:

```text
w = -G / (H + lambda)
```

где:

- `G` - сумма градиентов объектов в листе;
- `H` - сумма гессианов объектов в листе;
- `lambda` - L2-регуляризация.

Для бинарной классификации:

```text
g_i = p_i - y_i
h_i = p_i * (1 - p_i)
```

Градиенты/гессианы считаются при обучении для каждой строки на каждом boosting-шаге. При прогнозе новая строка просто проходит по уже построенным деревьям.

## Label leakage fix

Была подтверждена проблема label leakage на границе train/test в walk-forward.

Причина:

- `build_feature_dataset` считал target на всём датасете;
- затем `training.py` резал готовые `X/y` на train/test;
- последние `horizon` строк train имели target, рассчитанный по будущим свечам из test-window.

Исправление уже внесено:

- реализован purged split;
- в walk-forward обучение идёт до `train_end - horizon`;
- test-window начинается там же, где раньше;
- в обычном train/test split также исключаются последние `horizon` строк train перед test-set.

Файл:

```text
services/ml-service/app/services/training.py
```

Тесты:

```text
services/ml-service/tests/test_training_purged_split.py
```

Проверено:

- при `horizon=4`, `train_window=600` фактический `train_rows = 596`;
- последние `horizon` строк train не попадают в обучение;
- test-window начинается на прежней границе;
- backtest по-прежнему открывает сделку на следующей свече.

## Основная конфигурация диплома

Основная конфигурация выбрана на 4h, потому что она оказалась устойчивее.

```text
symbol: BTC-USDT
timeframe: 4h
date range: 19.04.2024 - 23.05.2026
horizon: 4
target: 0.010
entry threshold: 0.56
ATR: 1.5
RR: 2.0
mode: long_only / soft
train_window: 600
test_window: 120
max_folds: 35
```

Финальные результаты, которые использовались в дипломе:

```text
BTC 4h improved:
PnL: 26.09%
Winrate: 52.83%
Profit Factor: 1.845
Max Drawdown: 8.18%
Trades: 54
```

Сравнение с 1h:

```text
BTC 1h improved:
PnL: 10.01%
Winrate: 53.85%
Profit Factor: 1.345
Max Drawdown: 5.52%
Trades: 91
```

1h рабочая исследовательская конфигурация:

```text
BTC-USDT
timeframe: 1h
horizon: 6
target: 0.006
entry: 0.63
ATR: 1.25
RR: 1.25
mode: long_only / soft
```

## Выводы исследования

Кратко:

- BTC оказался стабильнее SOL;
- 5m, 15m, 30m слишком шумные;
- 1h даёт больше сделок, но чувствителен к комиссиям и шуму;
- 4h выбран как основная конфигурация;
- adaptive ATR SL/TP лучше фиксированных уровней;
- cooldown уменьшает шум/просадку, но сильно режет прибыль;
- re-arm в тестах был слишком ограничивающим;
- прибыль формируется кластерами импульсных движений;
- ML-метрики не равны торговой прибыльности.

## ML-метрики основной конфигурации

Примерные ML-метрики для основной конфигурации:

```text
Accuracy: 0.643
Precision: 0.281
Recall: 0.191
F1: 0.228
Target=1: 27.50%
```

Объяснение:

- `Accuracy` показывает долю правильных классификаций;
- `Precision` показывает, как часто прогнозы `target=1` оказались верными;
- `Recall` показывает, какую долю реальных `target=1` модель нашла;
- `F1` балансирует precision и recall;
- `Target=1` показывает долю положительного класса.

Важно писать:

> ML-метрики показывают качество классификации целевого события, а торговые метрики показывают результат стратегии после применения порога входа, фильтров, комиссий и риск-менеджмента.

## Рисунки для диплома

### Рисунок 1 - Архитектура программной системы

Основной контур:

```text
BingX API
-> Market Data Service
-> PostgreSQL / ML Service
-> Strategy Service
-> Risk Manager
-> Backtesting Service
-> Dashboard
```

Execution Service лучше показывать отдельно сбоку:

```text
Dashboard -> Execution Service -> PostgreSQL
```

Подпись:

```text
Рисунок 1 - Архитектура программной системы
```

### Рисунок 2 - Поток данных в системе

Вертикальный вид:

```text
BingX API
↓
Получение OHLCV-данных
↓
Формирование признаков
↓
Формирование target
↓
Обучение ML-модели
↓
Расчёт вероятности
↓
Генерация сигнала
↓
Risk Management (SL / TP / Time Exit)
↓
Backtesting
↓
Dashboard
```

### Рисунок 3 - ML Pipeline

```text
OHLCV-данные
-> расчёт признаков
-> формирование target
-> train/test или walk-forward split
-> обучение XGBoost
-> probability
-> entry threshold
-> signal candidate
```

### Рисунок 4 - Блок-схема торгового решения

```text
probability
-> entry threshold
-> фильтрация сигнала
-> BUY/HOLD
-> расчёт SL/TP
-> backtesting
-> причина выхода
```

### Рисунок 5 - Схема Walk-Forward Validation

Лучше рисовать вручную в Word фигурами:

```text
Train window 1  ----------->  Test window 1
                                  |
                                  | сдвиг окна
                                  v
Train window 2  ----------->  Test window 2
                                  |
                                  | сдвиг окна
                                  v
Train window 3  ----------->  Test window 3
```

## Видео-демонстрация

Проект на защите запускаться не будет, нужна видеодемонстрация 3-5 минут.

Сценарий:

1. Открыть dashboard.
2. Показать demo mode.
3. Показать основную конфигурацию BTC 4h.
4. Запустить или показать готовый walk-forward.
5. Показать вкладку Обзор: PnL, PF, Max DD, WR, Trades, equity, drawdown.
6. Показать Walk-forward.
7. Показать Сделки.
8. Показать Модель.
9. Закончить выводом: 4h выбран из-за более устойчивого поведения.

## Структура ВКР

Текущая логика структуры:

```text
Введение

1 Постановка задачи
1.1 Актуальность поставленной задачи
1.2 Постановка задачи

2 Аналитическая часть
2.1 Особенности криптовалютного фьючерсного рынка
2.2 Анализ существующих подходов к алгоритмической торговле
2.3 Анализ методов машинного обучения для финансовых временных рядов
2.4 Анализ методов тестирования торговых стратегий
2.5 Обоснование выбора технологий
2.6 Выводы по аналитической части

3 Конструкторская часть
3.1 Общая архитектура программной системы
3.2 Проектирование потока данных
3.3 Проектирование ML-pipeline
3.4 Проектирование торговой логики и риск-менеджмента
3.5 Проектирование механизма тестирования
3.6 Проектирование пользовательского интерфейса
3.7 Выводы по конструкторской части

4 Техническая часть
4.1 Стек технологий и среда разработки
4.2 Реализация сервиса получения рыночных данных
4.3 Реализация подсистемы формирования признаков
4.4 Реализация модели машинного обучения
4.5 Реализация сервиса генерации торговых сигналов
4.6 Реализация подсистемы управления рисками
4.7 Реализация backtesting и walk-forward testing
4.8 Реализация dashboard
4.9 Методика проведения исследований
4.10 Результаты тестирования
4.11 Анализ ограничений разработанной системы
4.12 Выводы по технической части

Заключение
Список использованных источников
Приложения
```

## Стиль текста для диплома

Писать:

- академично, но не канцеляритом;
- инженерно и реалистично;
- без “магического AI”;
- без обещаний гарантированной прибыли;
- с привязкой к реальным сервисам и результатам проекта.

Не писать:

- “ИИ предсказывает рынок”;
- “нейросеть”, если речь про XGBoost;
- “live trading” как реализованную функцию;
- “система гарантирует прибыль”;
- выдуманные результаты;
- выдуманные компоненты.

Если пользователь просит текст раздела ВКР, сначала уточнить:

- какой раздел;
- примерный объём;
- какие таблицы/рисунки уже есть;
- какие результаты использовать;
- нужен ли стиль как в ранее присланной ВКР.

Если пользователь просит “сразу текст”, можно писать без лишних вопросов, если контекст уже есть.

## Полезные команды

Проверка ML-service split tests:

```bash
/Users/xerogi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest services/ml-service/tests/test_training_purged_split.py
```

Проверка backtesting tests:

```bash
PYTHONPATH=services/backtesting-service /Users/xerogi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover services/backtesting-service/tests
```

Компиляция изменённых файлов:

```bash
/Users/xerogi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m py_compile services/ml-service/app/services/training.py services/ml-service/tests/test_training_purged_split.py
```

## Git / GitHub

Если пользователь хочет залить проект на GitHub:

- через сайт нельзя удобно загрузить больше 100 файлов;
- лучше использовать git или GitHub Desktop;
- репозиторий может быть приватным;
- перед заливкой проверить `.gitignore`.

Минимальный `.gitignore`:

```gitignore
__pycache__/
*.pyc
.env
.venv/
venv/
artifacts/
*.log
```

