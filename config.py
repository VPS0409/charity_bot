# config.py
import os
import logging

logger = logging.getLogger(__name__)

logger.info(f"DB_USER из окружения: '{os.getenv('DB_USER', '')}'")
logger.info(f"DB_PASSWORD из окружения: '{os.getenv('DB_PASSWORD', '')}'")

# ... остальные настройки ...

# Настройки базы данных
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'charity_bot_db')

# Настройки приложения
PORT = int(os.getenv('PORT', 5050))
MODEL_PATH = os.getenv('MODEL_PATH', 'models/all-MiniLM-L6-v2')
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.85))
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'