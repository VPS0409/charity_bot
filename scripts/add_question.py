import argparse
import logging
from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_single_question(intent, question, answer):
    """Добавляет один вопрос-ответ в базу данных"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    embedder = EmbeddingModel(config.MODEL_PATH)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к базе данных")
        return False

    try:
        # Проверяем существование вопроса
        if db.question_exists(question):
            logger.info(f"⏩ Вопрос уже существует: '{question}'")
            return False
        
        # Рассчитываем эмбеддинг
        embedding = embedder.get_embedding(question)
        blob = array_to_blob(embedding)
        
        # Добавляем ответ
        answer_id = db.insert_answer(answer)
        if not answer_id:
            logger.error("❌ Не удалось добавить ответ")
            return False
        
        # Добавляем вопрос
        if not db.insert_question(question, answer_id, blob, intent):
            logger.error("❌ Не удалось добавить вопрос")
            return False
        
        logger.info(f"✅ Вопрос успешно добавлен: '{question}'")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        return False
    finally:
        db.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Добавление единичного вопроса в базу данных')
    parser.add_argument('--intent', required=True, help='Намерение (intent) вопроса')
    parser.add_argument('--question', required=True, help='Текст вопроса')
    parser.add_argument('--answer', required=True, help='Текст ответа')
    
    args = parser.parse_args()
    
    if add_single_question(args.intent, args.question, args.answer):
        logger.info("🎉 Вопрос успешно добавлен в базу данных!")
    else:
        logger.error("💥 Не удалось добавить вопрос")