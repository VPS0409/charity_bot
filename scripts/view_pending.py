# view_pending.py
# view_pending.py

import logging
import argparse
import sys
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def view_pending_questions(show_all=False):
    """Показывает список неотвеченных вопросов"""
    # Используем позиционные аргументы для Database (как в add_question.py)
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к базе данных")
        return

    try:
        # Определяем условие для выборки
        condition = "" if show_all else "WHERE processed = FALSE"
        
        query = f"""
        SELECT 
            pq.id AS pending_id,
            uq.raw_question,
            uq.created_at,
            pq.processed,
            sq.title AS matched_question
        FROM pending_questions pq
        JOIN user_questions uq ON pq.user_question_id = uq.id
        LEFT JOIN standard_questions sq ON uq.standard_question_id = sq.id
        {condition}
        ORDER BY uq.created_at DESC
        """
        
        with db.connection.cursor() as cursor:
            cursor.execute(query)
            questions = cursor.fetchall()
            
            if not questions:
                logger.info("ℹ️ Нет неотвеченных вопросов")
                return
                
            logger.info(f"📋 Найдено {len(questions)} вопросов:")
            print("\n" + "=" * 100)
            print(f"{'ID':<8} | {'Статус':<12} | {'Дата создания':<20} | {'Вопрос'}")
            print("-" * 100)
            
            for row in questions:
                status = "Обработан" if row['processed'] else "Ожидает"
                date_str = row['created_at'].strftime("%Y-%m-%d %H:%M")
                matched = f" [Совпадение: {row['matched_question']}]" if row['matched_question'] else ""
                
                print(f"{row['pending_id']:<8} | {status:<12} | {date_str:<20} | {row['raw_question']}{matched}")
            
            print("=" * 100)
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
    finally:
        db.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Просмотр неотвеченных вопросов')
    parser.add_argument('--all', action='store_true', help='Показать все вопросы, включая обработанные')
    args = parser.parse_args()
    
    view_pending_questions(args.all)