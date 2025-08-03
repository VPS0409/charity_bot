# Файл load_initial_data.py
# Скрипт загрузки CSV в БД

import sys
import os
import argparse
import csv
import logging
import traceback
import re

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_header_row(row):
    """Определяет, является ли строка заголовком"""
    if len(row) < 3:
        return False
        
    # Проверяем, содержит ли строка только буквы (без цифр)
    contains_only_alpha = all(
        re.match(r'^[^\d]*$', field.strip(), re.IGNORECASE) 
        for field in row[:3]
    )
    
    # Проверяем наличие типичных слов заголовков
    header_keywords = ['intent', 'question', 'answer', 'вопрос', 'ответ', 'намерение']
    contains_keywords = any(
        any(keyword in field.lower() for keyword in header_keywords)
        for field in row[:3]
    )
    
    return contains_only_alpha or contains_keywords

def load_data(csv_file, has_header=False):
    """Загружает данные из CSV файла в базу данных"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    embedder = EmbeddingModel(config.MODEL_PATH)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к базе данных")
        return False

    row_count = 0
    inserted_count = 0
    skipped_count = 0
    actual_header = None
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Создаем CSV reader
            reader = csv.reader(file, delimiter=',', quotechar='"')
            
            # Читаем первую строку для анализа
            first_row = next(reader, None)
            if first_row is None:
                logger.error("❌ Файл CSV пуст")
                return False
                
            # Автоматически определяем, является ли первая строка заголовком
            auto_detected_header = is_header_row(first_row)
            
            # Если пользователь явно указал или автоматическое определение показало заголовок
            if has_header or auto_detected_header:
                actual_header = first_row
                logger.info(f"🔖 Обнаружен заголовок: {actual_header}")
            else:
                # Возвращаемся к началу файла
                file.seek(0)
                logger.info("ℹ️ Заголовок не обнаружен, первая строка считается данными")
            
            # Читаем оставшиеся строки
            for row in reader:
                row_count += 1
                
                if len(row) < 3:
                    logger.warning(f"⚠️ Строка {row_count}: не хватает данных - пропускаем")
                    skipped_count += 1
                    continue
                    
                intent = row[0].strip().replace('\xa0', ' ')  # Заменяем неразрывные пробелы
                question = row[1].strip().replace('\xa0', ' ')
                answer = row[2].strip().replace('\xa0', ' ')
                
                if not question or not answer:
                    logger.warning(f"⚠️ Строка {row_count}: пустой вопрос или ответ - пропускаем")
                    skipped_count += 1
                    continue
                
                try:
                    # Проверяем существование вопроса
                    if db.question_exists(question):
                        logger.info(f"⏩ Строка {row_count}: вопрос уже существует - '{question}'")
                        skipped_count += 1
                        continue
                    
                    # Рассчитываем эмбеддинг
                    embedding = embedder.get_embedding(question)
                    blob = array_to_blob(embedding)
                    
                    # Добавляем ответ и получаем его ID
                    answer_id = db.insert_answer(answer)
                    if not answer_id:
                        raise Exception("Не удалось добавить ответ")
                    
                    # Добавляем вопрос
                    if not db.insert_question(question, answer_id, blob, intent):
                        raise Exception("Не удалось добавить вопрос")
                    
                    inserted_count += 1
                    logger.info(f"✅ Строка {row_count}: добавлен вопрос - '{question}'")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке строки {row_count}: {str(e)}")
                    skipped_count += 1
                    continue
                
        logger.info(f"\n📊 Итоги по файлу {csv_file}:")
        logger.info(f"  Всего строк: {row_count}")
        logger.info(f"  Успешно добавлено: {inserted_count}")
        logger.info(f"  Пропущено: {skipped_count}")
        return inserted_count > 0
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    finally:
        db.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Загрузка данных из CSV в БД')
    parser.add_argument('--file', type=str, required=True, 
                        help='Путь к CSV файлу')
    parser.add_argument('--header', action='store_true',
                        help='Указать, если первая строка содержит заголовки столбцов')
    args = parser.parse_args()
    
    if load_data(args.file, args.header):
        logger.info("🎉 Данные успешно загружены в базу!")
    else:
        logger.error("💥 Загрузка данных завершилась с ошибками")