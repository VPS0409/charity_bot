import argparse
from database import Database
import config

def process_pending_questions(csv_output=None):
    db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    
    if not db.connect():
        return False
        
    # Получаем все необработанные вопросы
    cursor = db.execute_query("SELECT * FROM pending_questions")
    pending_questions = cursor.fetchall() if cursor else []
    
    if not pending_questions:
        print("🤷 Нет вопросов для обработки")
        return True
    
    # Если указан CSV файл - экспортируем в CSV
    if csv_output:
        import csv
        with open(csv_output, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Original Question', 'Normalized Question', 'Created At'])
            for pq in pending_questions:
                writer.writerow([pq[1], pq[2], pq[4]])
        print(f"📝 Экспортировано {len(pending_questions)} вопросов в {csv_output}")
    
    # Очищаем таблицу после обработки
    db.execute_query("TRUNCATE TABLE pending_questions")
    print(f"🧹 Очищена таблица pending_questions")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обработка неотвеченных вопросов')
    parser.add_argument('--csv', type=str, 
                        help='Экспортировать вопросы в CSV файл')
    args = parser.parse_args()
    
    if process_pending_questions(args.csv):
        print("✅ Обработка завершена успешно")
    else:
        print("❌ Ошибка при обработке вопросов")