# scripts/init_db.py
import sys
import os
import pymysql
import logging
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    connection = None
    try:
        logger.info(f"Подключение к БД: host={config.DB_HOST}, user={config.DB_USER}, db={config.DB_NAME}")
        
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Создаем базу данных, если не существует
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"База данных {config.DB_NAME} создана или уже существует")
            
            # Используем созданную базу данных
            cursor.execute(f"USE {config.DB_NAME}")
            
            # Таблица групп вопросов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица questions_groups создана")
            
            # Таблица ответов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    answer_text TEXT NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица answers создана")
            
            # Таблица стандартных вопросов (ранее главные вопросы)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS standard_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,          -- Формулировка вопроса для показа
                    group_id INT NOT NULL,                -- Связь с разделом
                    answer_id INT NOT NULL,               -- Ссылка на ответ
                    intent VARCHAR(255),                  -- Служебное название вопроса (опционально)
                    FOREIGN KEY (group_id) REFERENCES questions_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица standard_questions создана")
            
            # Таблица вариантов вопросов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS question_variants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    variant_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    standard_question_id INT NOT NULL,
                    FOREIGN KEY (standard_question_id) REFERENCES standard_questions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица question_variants создана")
            
            # Таблица вопросов без ответа
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    client_id VARCHAR(255),
                    raw_question TEXT NOT NULL,
                    normalized_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    standard_question_id INT,
                    answer_id INT,
                    is_found BOOLEAN DEFAULT FALSE,
                    confidence FLOAT,
                    response_time_ms INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (standard_question_id) REFERENCES standard_questions(id),
                    FOREIGN KEY (answer_id) REFERENCES answers(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица user_questions создана")

            # Создаем таблицу pending_questions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_question_id INT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    operator_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_question_id) REFERENCES user_questions(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            logger.info("Таблица pending_questions создана")
                    
            # Создаем индексы для производительности
            cursor.execute("CREATE INDEX idx_standard_questions_group ON standard_questions(group_id)")
            cursor.execute("CREATE INDEX idx_variants_standard_question ON question_variants(standard_question_id)")
            logger.info("Индексы созданы")
        
        connection.commit()
        logger.info("Все таблицы успешно созданы")
        return True
        
    except pymysql.Error as e:
        logger.error(f"Ошибка инициализации базы данных: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()
            logger.info("Соединение с БД закрыто")

if __name__ == "__main__":
    if init_database():
        logger.info("✅ База данных успешно инициализирована")
        sys.exit(0)
    else:
        logger.error("❌ Ошибка инициализации базы данных")
        sys.exit(1)