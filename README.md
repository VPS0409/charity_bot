# Инструкция по развертыванию Charity Bot

## Требования
- Python 3.11+
- MySQL 8.0+ (или Docker)
- pip

## Установка

  1. Клонирование репозитория

bash
git clone https://github.com/VPS0409/charity_bot.git
cd charity_bot

  2. Настройка окружения

bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

  3. Установка зависимостей

bash
pip install -r requirements.txt

  4. Настройка конфигурации

Создайте файл .env на основе .env.example:

bash
cp .env.example .env

Отредактируйте .env вашими реальными настройками.

  5. Загрузка модели

bash
python download_model.py

  6. Инициализация базы данных

bash
python init_db.py

  7. Запуск приложения

  bash
python app.py

Запуск через Docker

bash
docker-compose up --build

Проверка работы

bash
curl -X POST http://localhost:5050/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Как получить помощь?"}'


