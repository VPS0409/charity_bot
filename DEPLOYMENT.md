Полная инструкция по установке и первоначальной настройке

Уважаемые коллеги!
Для запуска проекта Charity Bot, пожалуйста, выполните следующие шаги:

1. Клонирование репозитория:

bash
git clone https://github.com/VPS0409/charity_bot.git
cd charity_bot
2. Установка зависимостей:

bash
pip install -r requirements.txt
3. Загрузка ML-модели (не включена в репозиторий из-за размера):

bash
mkdir -p models/all-MiniLM-L6-v2
Вариант A: Автоматическая загрузка (требуется интернет):

bash
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('models/all-MiniLM-L6-v2')
"
Вариант B: Ручная загрузка:

Скачайте архив модели:
https://public.ukp.informatik.tu-darmstadt.de/reimers/sentence-transformers/v0.2/all-MiniLM-L6-v2.zip

Распакуйте в папку: charity_bot/models/all-MiniLM-L6-v2

4. Настройка базы данных:

Создайте БД MySQL:

sql
CREATE DATABASE charity_bot;
CREATE USER 'bot_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON charity_bot.* TO 'bot_user'@'localhost';
Настройте подключение в .env:

ini
DB_HOST=localhost
DB_USER=bot_user
DB_PASS=secure_password
DB_NAME=charity_bot
5. Инициализация базы данных:

bash
flask db init
flask db migrate -m "Initial tables"
flask db upgrade
6. Загрузка тестовых данных:

bash
python scripts/load_data.py
7. Запуск сервера:

bash
flask run --host=0.0.0.0 --port=5000
8. Проверка работы:

bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Как получить коляску?"}'
