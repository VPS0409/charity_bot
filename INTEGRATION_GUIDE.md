
---

**INTEGRATION_GUIDE.md**  
Проверим содержание:

# Руководство по интеграции с API Charity Bot

## Базовый URL
`http://ваш-сервер:5050`

## Эндпоинты

### `POST /ask`
- **Описание**: Основной метод для вопросов к боту
- **Параметры запроса**:
  ```json
  {
    "question": "Текст вопроса"
  }

  Пример ответа:

  {
  "answer": "Для получения помощи обратитесь...",
  "intent": "medical_help",
  "confidence": 0.92
}

  Пример кода (JavaScript)

async function askBot(question) {
  const response = await fetch('http://localhost:5050/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  return await response.json();
}

// Использование
askBot("Как получить лекарства?").then(data => {
  console.log("Ответ бота:", data.answer);
});


Важные примечания
Для работы требуется предварительная настройка (см. README.md)

В продакшене замените localhost на ваш домен

Все настройки сервера через .env файл

text

---

**3. requirements.txt**  
Убедимся в актуальности зависимостей. Должен содержать:
Flask==2.3.2
torch==2.7.1
transformers==4.54.1
sentence-transformers==2.2.2
pymysql==1.1.0
python-dotenv==1.0.1
huggingface-hub==0.22.2
numpy==1.26.4

text

Для проверки:
```bash
pip list --format=freeze > current_requirements.txt
diff requirements.txt current_requirements.txt
4. Виртуальное окружение (.venv)
Убедимся, что:

Каталог .venv добавлен в .gitignore

В инструкциях есть команды для создания нового окружения

Не содержит системно-специфичных путей

5. Вспомогательные файлы
Проверим наличие:

.env.example - шаблон конфигурации

.gitignore - должен исключать:

text
.env
.venv
__pycache__/
*.pyc
.DS_Store
download_model.py - скрипт загрузки модели

init_db.py - скрипт инициализации БД

6. Docker-конфигурация
Проверим Dockerfile и docker-compose.yml:

dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python download_model.py

EXPOSE 5050
CMD ["python", "app.py"]
yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5050:5050"
    environment:
      - DB_HOST=db
      - DB_USER=bot_user
      - DB_PASSWORD=secure_password
      - DB_NAME=charity_bot_db
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: charity_bot_db
      MYSQL_USER: bot_user
      MYSQL_PASSWORD: secure_password
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
