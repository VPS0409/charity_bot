# check_mysql_functions.py
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath('.'))

import config
from database import Database

def check_mysql_functions():
    """Проверяем доступные функции MySQL"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    
    conn = db._get_connection()
    if not conn:
        print("❌ Не удалось подключиться к БД")
        return
    
    try:
        with conn.cursor() as cursor:
            # Проверим доступность COSINE_DISTANCE
            try:
                cursor.execute("SELECT COSINE_DISTANCE(1, 1)")
                result = cursor.fetchone()
                print("✅ COSINE_DISTANCE доступна")
            except Exception as e:
                print(f"❌ COSINE_DISTANCE не доступна: {e}")
            
            # Проверим структуру таблицы question_variants
            cursor.execute("DESCRIBE question_variants")
            columns = cursor.fetchall()
            print("\nСтруктура question_variants:")
            for col in columns:
                print(f"  {col['Field']} - {col['Type']}")
            
            # Проверим есть ли данные в таблице
            cursor.execute("SELECT COUNT(*) as count FROM question_variants")
            count = cursor.fetchone()['count']
            print(f"\nКоличество вариантов вопросов: {count}")
            
            # Проверим несколько записей
            cursor.execute("SELECT standard_question_id, variant_text FROM question_variants LIMIT 5")
            samples = cursor.fetchall()
            print("\Примеры вопросов:")
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. ID: {sample['standard_question_id']}, Текст: {sample['variant_text'][:50]}...")
                
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_mysql_functions()