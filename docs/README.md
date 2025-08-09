<!-- Файл README.md -->
README.md
markdown
# Charity Bot for Children's Charity Foundation

Чат-бот для сайта благотворительного фонда помощи безнадежно больным детям.

## Установка

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/VPS0409/charity_bot.git
cd charity_bot
Создайте и активируйте виртуальное окружение:

bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
Установите зависимости:

bash
pip install -r requirements.txt
Загрузите модель:

bash
python download_model.py
Инициализируйте базу данных:

bash
python scripts/init_db.py
Загрузите данные:

bash
python scripts/load_data.py --file base_qu_an/qu_ans_1.csv --header
Запустите сервер:

bash
python app.py
Docker-установка
Соберите образ:

bash
docker-compose build
Запустите сервисы:

bash
docker-compose up

Проверка работы

bash
curl -X POST http://localhost:5050/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Как получить помощь?"}'

  Использование
Проверка работы сервера
bash
curl http://localhost:5050

Тестовый запрос
bash
curl http://localhost:5050/test_similarity

Основной функционал
bash
curl -X POST http://localhost:5050/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"Как сделать пожертвование?"}'

Управление данными
Скрипты
scripts/init_db.py - инициализация БД

scripts/load_data.py - загрузка данных из CSV

scripts/add_question.py - добавление вопроса

scripts/view_pending.py - просмотр ожидающих вопросов

scripts/process_pending.py - обработка ожидающих вопросов

Подробнее в документации скриптов.

Конфигурация
Настройки приложения в файле .env (создайте на основе .env.example).

load_data.py
Загружает данные из CSV-файла в базу.

bash
python scripts/load_data.py --file base_qu_an/qu_ans_1.csv --header
add_question.py
Добавляет один вопрос в базу данных.

bash
python scripts/add_question.py --question "Как стать волонтером?" --answer "Заполните форму на нашем сайте" --intent "volunteering"
view_pending.py
Просмотр необработанных вопросов.

bash
python scripts/view_pending.py
process_pending.py
Обработка неотвеченных вопросов.

bash
python scripts/process_pending.py --id 5 --answer "Ответ на вопрос" --intent "new_intent"
text

### 9. Финальная структура проекта
charity_bot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── app.py
├── config.py
├── database.py
├── download_model.py
├── Dockerfile
├── docker-compose.yml
├── embedding_model.py
├── utils.py
├── scripts/
│ ├── init_db.py
│ ├── load_data.py
│ ├── add_question.py
│ ├── process_pending.py
│ └── view_pending.py
├── base_qu_an/
│ └── qu_ans_1.csv
├── docs/
│ ├── INTEGRATION_GUIDE.md
│ ├── SCRIPTS.md
│ └── ARCHITECTURE.md
└── models/ (будет создан после download_model.py)
└── all-MiniLM-L6-v2/

