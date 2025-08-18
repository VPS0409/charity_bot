README.md
markdown
# Charity Bot for Children's Charity Foundation

Чат-бот для сайта благотворительного фонда помощи безнадежно больным детям.

## Особенности
- Двухуровневая система вопросов (разделы → стандартные вопросы)
- NLP-поиск похожих вопросов с использованием модели `all-MiniLM-L6-v2`
- Логирование всех вопросов пользователей для аналитики
- Администрирование базы знаний через скрипты
- Поддержка Docker

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
Тестовый запрос схожести
bash
curl http://localhost:5050/test_similarity
Основной функционал
bash
curl -X POST http://localhost:5050/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"Как сделать пожертвование?"}'
Управление данными
Скрипты
Скрипт	Описание	Пример использования
init_db.py	Инициализация структуры БД	python scripts/init_db.py
load_data.py	Загрузка данных из CSV	python scripts/load_data.py --file data.csv --header
add_question.py	Добавление вопроса	python scripts/add_question.py --group "Раздел" --intent "new_intent" --question "Вопрос" --answer "Ответ"
view_pending.py	Просмотр неотвеченных вопросов	python scripts/view_pending.py
process_pending.py	Обработка неотвеченных вопросов	python scripts/process_pending.py --id 5 --answer "Ответ" --intent "new_intent"
Подробнее в документации скриптов.

Конфигурация
Настройки приложения задаются в файле .env (создайте на основе .env.example):

ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=charity_bot_db
DB_USER=charity_user
DB_PASSWORD=secure_password
MODEL_PATH=models/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.75
PORT=5050
DEBUG=True
Структура проекта
text
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
│   ├── init_db.py
│   ├── load_data.py
│   ├── add_question.py
│   ├── process_pending.py
│   └── view_pending.py
├── base_qu_an/
│   └── qu_ans_1.csv
├── docs/
│   ├── INTEGRATION_GUIDE.md
│   ├── SCRIPTS.md
│   └── ARCHITECTURE.md
└── models/
    └── all-MiniLM-L6-v2/  # создается после download_model.py



Оценка необходимых ресурсов:
1. Оперативная память (ОЗУ):

Минимально: 1 ГБ

Рекомендуемо: 2-4 ГБ

Для комфортной работы: 4+ ГБ

Обоснование:

Модель all-MiniLM-L6-v2: ~200-300 МБ в памяти

Веб-сервер (Flask) + Workers: 300-500 МБ

База данных (MySQL): 500+ МБ

Запас для операционной системы и фоновых процессов

2. Дисковое пространство:

Минимально: 2 ГБ

Рекомендуемо: 5-10 ГБ

Для долгосрочной работы: 20+ ГБ

Обоснование:

Модель all-MiniLM-L6-v2: 80 МБ

Код приложения: 100-200 МБ

База данных (начальная): 100-500 МБ

Логи и бэкапы: 1+ ГБ

Запас для роста базы данных (вопросы/ответы)

3. Процессор (ядра):

Минимально: 1 ядро

Рекомендуемо: 2-4 ядра

Для высокой нагрузки: 4+ ядер

Обоснование:

Векторизация вопросов (CPU-bound операция)

Параллельная обработка запросов

Фоновые задачи (обработка очереди вопросов)

4. Сетевые ресурсы:

Пропускная способность: 10+ Мбит/с

Ежемесячный трафик: 50+ ГБ (зависит от активности)

Типовые сценарии развёртывания:
1. Тестовый сервер (до 100 пользователей/день):

ОЗУ: 1-2 ГБ

Диск: 5 ГБ SSD

CPU: 1-2 ядра

Стоимость: $5-10/мес (например, DigitalOcean Basic Droplet)

2. Продакшн-сервер (до 1000 пользователей/день):

ОЗУ: 4 ГБ

Диск: 20 ГБ SSD

CPU: 2-4 ядра

Стоимость: $20-40/мес (например, AWS t3.medium)

3. Высоконагруженное решение (5000+ пользователей/день):

ОЗУ: 8+ ГБ

Диск: 50+ ГБ SSD

CPU: 4+ ядер

Балансировщик нагрузки

Отдельный сервер для базы данных

Стоимость: $100+/мес

Оптимизационные рекомендации:
Кэширование:

Redis для кэширования частых запросов

Memcached для сессий пользователей

Асинхронная обработка:

Celery/RQ для фоновой обработки вопросов

Асинхронные workers для Flask

Масштабирование:

Вертикальное: увеличение ресурсов сервера

Горизонтальное: добавление новых инстансов

Мониторинг:

Prometheus + Grafana для отслеживания метрик

Sentry для отслеживания ошибок

Логирование в ELK-стек

Оценка роста ресурсов:
Параметр	Начало	Через 6 мес	Через 1 год
Пользователи/день	100	500	2000+
Вопросов/день	50	300	1000+
Размер БД	200 МБ	1 ГБ	5+ ГБ
Пиковая ОЗУ	1 ГБ	2 ГБ	4+ ГБ
Начните с минимальной конфигурации (2 ГБ ОЗУ, 2 ядра, 10 ГБ SSD) - её будет достаточно для старта. По мере роста нагрузки вы сможете легко масштабировать ресурсы в облачной среде.
