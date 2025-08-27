# scripts/load_data.py
import sys
import os
import argparse
import csv
import logging
import traceback
import re
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_field(value):
    """Нормализация и очистка полей"""
    if value is None:
        return ""
    return str(value).strip().replace('\xa0', ' ').replace('"', '').replace("'", "")

def is_header_row(row):
    """Определяет, является ли строка заголовком"""
    header_keywords = [
        'questions_groups', 'standard_questions', 
        'intent', 'question_variants', 'answers'
    ]
    contains_keywords = any(
        any(keyword in str(field).lower() for keyword in header_keywords)
        for field in row
    )
    return contains_keywords

def load_data(csv_file, has_header=False):
    """Загружает данные из CSV файла в базу данных"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    embedder = EmbeddingModel(config.MODEL_PATH)
    
    # Кэши для избежания дублирования
    groups_cache = {}
    std_questions_cache = {}
    answers_cache = {}
    variants_cache = {}  # Кэш для отслеживания обработанных вариантов
    
    row_count = 0
    inserted_groups = 0
    inserted_std_questions = 0
    inserted_answers = 0
    inserted_variants = 0
    skipped_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"')
            
            # Определение заголовка
            first_row = next(reader, None)
            if first_row is None:
                logger.error("❌ Файл CSV пуст")
                return False
                
            auto_detected_header = is_header_row(first_row)
            
            if has_header or auto_detected_header:
                actual_header = first_row
                logger.info(f"🔖 Обнаружен заголовок: {actual_header}")
            else:
                file.seek(0)
                logger.info("ℹ️ Заголовок не обнаружен, первая строка считается данными")
            
            for row in reader:
                row_count += 1
                
                # Проверка минимального количества полей
                if len(row) < 5:
                    logger.warning(f"⚠️ Строка {row_count}: не хватает данных (требуется 5 полей) - пропускаем")
                    skipped_count += 1
                    continue
                    
                # Обработка полей
                group_name = normalize_field(row[0])
                std_question = normalize_field(row[1])
                intent = normalize_field(row[2])
                variant_text = normalize_field(row[3])
                answer_text = normalize_field(row[4])
                
                # Проверка обязательных полей
                if not group_name or not std_question or not answer_text:
                    logger.warning(f"⚠️ Строка {row_count}: пустое обязательное поле - пропускаем")
                    skipped_count += 1
                    continue
                
                try:
                    # 1. Обработка группы вопросов
                    if group_name not in groups_cache:
                        # Получаем или создаем группу
                        groups = db.get_question_groups()
                        group_id = None
                        
                        # Ищем существующую группу
                        for group in groups:
                            if group['name'] == group_name:
                                group_id = group['id']
                                break
                        
                        # Если группа не найдена, создаем новую
                        if group_id is None:
                            group_id = db.insert_group(group_name)
                            if not group_id:
                                logger.warning(f"⚠️ Не удалось создать группу: {group_name}")
                                skipped_count += 1
                                continue
                                
                        groups_cache[group_name] = group_id
                        inserted_groups += 1
                        logger.info(f"➕ Группа найдена/добавлена: {group_name}")
                    else:
                        group_id = groups_cache[group_name]
                    
                    # 2. Обработка ответа
                    if answer_text not in answers_cache:
                        # Получаем все ответы
                        answers = db.get_all_answers()
                        answer_id = None
                        
                        # Ищем существующий ответ
                        for answer in answers:
                            if answer['text'] == answer_text:
                                answer_id = answer['id']
                                break
                        
                        # Если ответ не найден, создаем новый
                        if answer_id is None:
                            answer_id = db.insert_answer(answer_text)
                            if not answer_id:
                                logger.warning(f"⚠️ Не удалось создать ответ: {answer_text[:50]}...")
                                skipped_count += 1
                                continue
                                
                        answers_cache[answer_text] = answer_id
                        inserted_answers += 1
                        logger.info(f"➕ Ответ найден/добавлен: {answer_text[:50]}...")
                    else:
                        answer_id = answers_cache[answer_text]
                    
                    # 3. Обработка стандартного вопроса
                    cache_key = f"{group_id}_{std_question}"
                    if cache_key not in std_questions_cache:
                        # Получаем все стандартные вопросы
                        questions = db.get_all_standard_questions()
                        standard_question_id = None
                        
                        # Ищем существующий вопрос
                        for question in questions:
                            if (question['group_id'] == group_id and 
                                question['title'] == std_question):
                                standard_question_id = question['id']
                                break
                        
                        # Если вопрос не найден, создаем новый
                        if standard_question_id is None:
                            standard_question_id = db.insert_standard_question(std_question, group_id, answer_id, intent)
                            if not standard_question_id:
                                logger.warning(f"⚠️ Не удалось создать стандартный вопрос: {std_question}")
                                skipped_count += 1
                                continue
                                
                        std_questions_cache[cache_key] = standard_question_id
                        inserted_std_questions += 1
                        logger.info(f"➕ Стандартный вопрос найден/добавлен: {std_question}")
                    else:
                        standard_question_id = std_questions_cache[cache_key]
                    
                    # 4. Обработка варианта вопроса (если указан)
                    if variant_text:
                        # Проверяем, не обрабатывали ли уже этот вариант
                        variant_cache_key = f"{standard_question_id}_{variant_text}"
                        if variant_cache_key in variants_cache:
                            logger.info(f"⏩ Вариант уже обработан: '{variant_text}'")
                            continue
                            
                        variants_cache[variant_cache_key] = True
                        
                        # Нормализация и эмбеддинг
                        normalized_text = embedder.normalize_text(variant_text)
                        embedding = embedder.get_embedding(normalized_text)
                        blob = array_to_blob(embedding)
                        
                        # Вставка варианта
                        try:
                            success = db.insert_question_variant(variant_text, blob, standard_question_id)
                            if success:
                                inserted_variants += 1
                                logger.info(f"✅ Вариант добавлен: '{variant_text}'")
                            else:
                                logger.warning(f"⚠️ Вариант не добавлен (дубликат): '{variant_text}'")
                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка при добавлении варианта '{variant_text}': {str(e)}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке строки {row_count}: {str(e)}")
                    logger.debug(traceback.format_exc())
                    skipped_count += 1
                    continue
                
        logger.info(f"\n📊 Итоги загрузки {csv_file}:")
        logger.info(f"  Всего строк: {row_count}")
        logger.info(f"  Добавлено групп: {inserted_groups}")
        logger.info(f"  Добавлено ответов: {inserted_answers}")
        logger.info(f"  Добавлено стандартных вопросов: {inserted_std_questions}")
        logger.info(f"  Добавлено вариантов: {inserted_variants}")
        logger.info(f"  Пропущено строк: {skipped_count}")
        return True
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        logger.error(traceback.format_exc())
        return False

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