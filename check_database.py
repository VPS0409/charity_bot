#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.abspath('.'))

import config
from database import Database

# Инициализация базы данных
db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)

def check_database():
    print("=" * 60)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Проверим основные таблицы
    tables_to_check = [
        'questions_groups',
        'standard_questions', 
        'answers',
        'question_variants',
        'user_questions',
        'pending_questions'
    ]
    
    for table in tables_to_check:
        try:
            result = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            if result:
                count = result[0]['count']
                print(f"✓ {table}: {count} записей")
            else:
                print(f"✗ {table}: нет данных или ошибка")
        except Exception as e:
            print(f"✗ {table}: ошибка - {e}")
    
    print("\n" + "=" * 60)
    print("ПОИСК ВОПРОСОВ С ТЕКСТОМ 'ПСИХИАТР'")
    print("=" * 60)
    
    # Поиск вопросов с текстом "психиатр"
    try:
        result = db.execute_query("""
            SELECT 
                qv.variant_text,
                sq.title as standard_question,
                a.answer_text,
                sq.intent
            FROM question_variants qv
            JOIN standard_questions sq ON qv.standard_question_id = sq.id
            JOIN answers a ON sq.answer_id = a.id
            WHERE qv.variant_text LIKE %s OR sq.title LIKE %s
        """, ('%психиатр%', '%психиатр%'))
        
        if result:
            print(f"Найдено {len(result)} вопросов:")
            for i, row in enumerate(result, 1):
                print(f"\n{i}. Вариант вопроса: {row['variant_text']}")
                print(f"   Стандартный вопрос: {row['standard_question']}")
                print(f"   Intent: {row['intent']}")
                print(f"   Ответ: {row['answer_text'][:100]}...")
        else:
            print("Вопросы с текстом 'психиатр' не найдены")
            
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
    
    print("\n" + "=" * 60)
    print("ПОРЫ СХОЖЕСТИ И НАСТРОЙКИ")
    print("=" * 60)
    
    print(f"Порог схожести (SIMILARITY_THRESHOLD): {config.SIMILARITY_THRESHOLD}")
    print(f"Путь к модели: {config.MODEL_PATH}")
    print(f"База данных: {config.DB_NAME}")
    print(f"Хост БД: {config.DB_HOST}")

if __name__ == "__main__":
    check_database()