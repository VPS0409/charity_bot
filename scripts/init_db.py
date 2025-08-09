# init_db.py
import pymysql
import os
import logging
import sys
from dotenv import load_dotenv  # Импортируем загрузчик для .env

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    connection = None
    try:
        # Получаем значения из переменных окружения
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_USER = os.getenv('DB_USER', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_NAME = os.getenv('DB_NAME', 'charity_bot_db')
        
        logger.info(f"Попытка подключения к MySQL: user={DB_USER}, host={DB_HOST}")
        
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Создание базы данных
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            logger.info(f"База данных '{DB_NAME}' создана или уже существует")
        
        logger.info("Инициализация БД успешно завершена")
        return True
        
    except pymysql.Error as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return False
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    init_database()