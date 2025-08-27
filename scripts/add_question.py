# файл scripts/add_question.py

import argparse
import logging
import sys
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_single_question(group_name, intent, question, answer):
    """Добавляет один вопрос-ответ в новую структуру базы данных"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    embedder = EmbeddingModel(config.MODEL_PATH)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к базе данных")
        return False

    try:
        # 1. Обработка группы
        group_id = db.get_or_create_group(group_name)
        if not group_id:
            logger.error(f"❌ Не удалось найти или создать группу: '{group_name}'")
            return False
        logger.info(f"✅ Группа: '{group_name}' (ID: {group_id})")

        # 2. Обработка ответа
        answer_id = db.insert_answer(answer)
        if not answer_id:
            logger.error("❌ Не удалось добавить ответ")
            return False
        logger.info(f"✅ Ответ добавлен (ID: {answer_id})")

        # 3. Обработка стандартного вопроса
        std_question_id = db.insert_standard_question(
            title=question,
            group_id=group_id,
            answer_id=answer_id,
            intent=intent
        )
        if not std_question_id:
            logger.error("❌ Не удалось добавить стандартный вопрос")
            return False
        logger.info(f"✅ Стандартный вопрос добавлен (ID: {std_question_id})")

        # 4. Обработка варианта вопроса
        normalized_text = embedder.normalize_text(question)
        embedding = embedder.get_embedding(normalized_text)
        blob = array_to_blob(embedding)
        
        if db.insert_question_variant(
            variant_text=question,
            embedding=blob,
            std_question_id=std_question_id
        ):
            logger.info(f"✅ Вариант вопроса добавлен: '{question}'")
        else:
            logger.warning(f"⚠️ Вариант не добавлен (возможно дубликат): '{question}'")

        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        return False
    finally:
        db.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Добавление единичного вопроса в базу данных')
    parser.add_argument('--group', required=True, help='Название группы/раздела')
    parser.add_argument('--intent', required=True, help='Служебное название вопроса (intent)')
    parser.add_argument('--question', required=True, help='Текст вопроса')
    parser.add_argument('--answer', required=True, help='Текст ответа')
    
    args = parser.parse_args()
    
    if add_single_question(args.group, args.intent, args.question, args.answer):
        logger.info("🎉 Вопрос успешно добавлен в базу данных!")
    else:
        logger.error("💥 Не удалось добавить вопрос")