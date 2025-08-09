# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY . .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Загрузка модели при сборке
RUN python download_model.py

# Инициализация базы данных при запуске
CMD bash -c "python scripts/init_db.py && python app.py"