# scripts/process_pending.py

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
import config
from add_question import add_single_question  # Исправленный импорт

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_questions(question_ids=None, all_flag=False):
    """Обрабатывает вопросы в интерактивном или пакетном режиме"""
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    
    if not db.connect():
        logger.error("❌ Ошибка подключения к БД")
        return False

    try:
        # Выборка вопросов для обработки
        if all_flag:
            query = "SELECT pq.id, uq.raw_question FROM pending_questions pq JOIN user_questions uq ON pq.user_question_id = uq.id WHERE pq.processed = FALSE"
        elif question_ids:
            ids_str = ",".join(map(str, question_ids))
            query = f"SELECT pq.id, uq.raw_question FROM pending_questions pq JOIN user_questions uq ON pq.user_question_id = uq.id WHERE pq.id IN ({ids_str})"
        else:
            # Интерактивный режим - все необработанные вопросы
            query = "SELECT pq.id, uq.raw_question FROM pending_questions pq JOIN user_questions uq ON pq.user_question_id = uq.id WHERE pq.processed = FALSE"
        
        with db.connection.cursor() as cursor:
            cursor.execute(query)
            questions = cursor.fetchall()
            
            if not questions:
                logger.info("ℹ️ Нет вопросов для обработки")
                return True

            logger.info(f"🔧 Начато обновление {len(questions)} вопросов...")
            
            for q in questions:
                question_text = q['raw_question']
                logger.info(f"\n❓ Вопрос ID {q['id']}: {question_text}")
                
                # Интерактивный режим
                print("\nВыберите действие:")
                print("1 - Добавить как новый вопрос-ответ")
                print("2 - Привязать к существующему вопросу")
                print("3 - Пропустить")
                choice = input("Ваш выбор (1/2/3): ").strip()
                
                if choice == "1":
                    # Добавление нового вопроса
                    answer = input("Введите ответ для нового вопроса: ").strip()
                    intent = input("Введите служебное название вопроса (intent): ").strip()
                    group_name = input("Введите название группы вопросов (опционально, нажмите Enter чтобы пропустить): ").strip()
                    
                    if add_single_question(
                        group=group_name or "Общие вопросы",
                        intent=intent,
                        question=question_text,
                        answer=answer
                    ):
                        logger.info("✅ Вопрос добавлен")
                    else:
                        logger.error("❌ Ошибка добавления вопроса")
                        continue
                elif choice == "2":
                    # Привязка к существующему вопросу
                    std_question_id = input("Введите ID стандартного вопроса: ").strip()
                    if not std_question_id.isdigit():
                        logger.error("⚠️ Некорректный ID вопроса")
                        continue
                    # Обновляем привязку
                    update_query = "UPDATE user_questions SET standard_question_id = %s WHERE id = (SELECT user_question_id FROM pending_questions WHERE id = %s)"
                    cursor.execute(update_query, (int(std_question_id), q['id']))
                    db.connection.commit()
                elif choice == "3":
                    logger.info("⏭️ Вопрос пропущен")
                    continue
                else:
                    logger.error("⚠️ Некорректный выбор")
                    continue
                
                # Помечаем как обработанный
                cursor.execute("UPDATE pending_questions SET processed = TRUE WHERE id = %s", (q['id'],))
                db.connection.commit()
                logger.info(f"🆗 Вопрос ID {q['id']} обработан")
            
            return True
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        return False
    finally:
        db.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обработка неотвеченных вопросов')
    parser.add_argument('--ids', type=str, help='ID вопросов через запятую (например: 1,2,3)')
    parser.add_argument('--all', action='store_true', help='Обработать все неотвеченные вопросы')
    args = parser.parse_args()
    
    # Преобразование ID
    question_ids = None
    if args.ids:
        try:
            question_ids = list(map(int, args.ids.split(',')))
        except ValueError:
            logger.error("⚠️ Ошибка формата ID. Используйте числа через запятую (1,2,3)")
            sys.exit(1)
    
    success = process_questions(
        question_ids=question_ids,
        all_flag=args.all
    )
    
    if not success:
        logger.error("❌ Завершено с ошибками")
        sys.exit(1)
    logger.info("✅ Все операции успешно завершены")