import logging
from database import Database
import config
from utils import blob_to_array
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def view_pending_questions():
    """Показывает список неотвеченных вопросов"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к базе данных")
        return

    try:
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pending_questions ORDER BY created_at DESC")
        questions = cursor.fetchall()
        
        if not questions:
            logger.info("ℹ️ Нет неотвеченных вопросов")
            return
            
        logger.info(f"📋 Найдено {len(questions)} неотвеченных вопросов:")
        print("\n" + "=" * 80)
        
        for i, question in enumerate(questions, 1):
            print(f"{i}. [ID: {question['id']}] [{question['created_at']}]")
            print(f"   Оригинальный вопрос: {question['original_question']}")
            print(f"   Нормализованный: {question['normalized_question']}")
            print("-" * 80)
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
    finally:
        cursor.close()
        db.disconnect()

if __name__ == '__main__':
    view_pending_questions()