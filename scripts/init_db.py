# scripts/init_db.py
import sys
import os
import pymysql
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Создаем базу данных, если не существует
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
            logger.info(f"База данных {config.DB_NAME} создана или уже существует")
            
            # Используем созданную базу данных
            cursor.execute(f"USE {config.DB_NAME}")
            
            # Создаем таблицы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    answer_text TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    answer_id INT NOT NULL,
                    embedding BLOB NOT NULL,
                    intent VARCHAR(255) NOT NULL,
                    FOREIGN KEY (answer_id) REFERENCES answers(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    original_text TEXT NOT NULL,
                    normalized_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Таблицы успешно созданы")
        
        connection.commit()
        return True
        
    except pymysql.Error as e:
        logger.error(f"Ошибка инициализации базы данных: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    if init_database():
        logger.info("✅ База данных успешно инициализирована")
        sys.exit(0)
    else:
        logger.error("❌ Ошибка инициализации базы данных")
        sys.exit(1)