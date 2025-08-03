# config.py

import os

# Настройки БД
DB_HOST = "localhost"
DB_USER = "charity_user"
DB_PASSWORD = "VPScharity0409$"
DB_NAME = "charity_bot_db"

# Настройки порта
PORT = 5050

# Модель эмбеддингов
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "all-MiniLM-L6-v2")
# MODEL_PATH = "cointegrated/LaBSE-en-ru"  # Легкая кросс-язычная модель

# Порог схожести вопросов
SIMILARITY_THRESHOLD = 0.85