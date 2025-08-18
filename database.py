# database.py

import pymysql
import logging
import numpy as np
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        self.connection = None
    
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("✅ Подключение к БД успешно установлено")
            return True
        except pymysql.Error as e:
            logger.error(f"❌ Ошибка подключения к БД: {str(e)}")
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с БД закрыто")
    
    # Основные методы для работы с данными
    def get_or_create_group(self, group_name, description=None):
        """Возвращает ID группы, создает если не существует"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT id FROM questions_groups WHERE name = %s"
                cursor.execute(query, (group_name,))
                result = cursor.fetchone()
                
                if result:
                    return result['id']
                else:
                    insert_query = "INSERT INTO questions_groups (name, description) VALUES (%s, %s)"
                    cursor.execute(insert_query, (group_name, description))
                    self.connection.commit()
                    return cursor.lastrowid
        except pymysql.Error as e:
            logger.error(f"❌ Ошибка в get_or_create_group: {str(e)}")
            return None
    
    def insert_answer(self, answer_text):
        """Добавляет ответ и возвращает его ID"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = "INSERT INTO answers (answer_text) VALUES (%s)"
                cursor.execute(query, (answer_text,))
                self.connection.commit()
                return cursor.lastrowid
        except pymysql.Error as e:
            logger.error(f"❌ Ошибка при добавлении ответа: {str(e)}")
            return None
    
    def insert_standard_question(self, title, group_id, answer_id, intent=None):
        """Добавляет стандартный вопрос"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = """
                INSERT INTO standard_questions (title, group_id, answer_id, intent)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (title, group_id, answer_id, intent))
                self.connection.commit()
                return cursor.lastrowid
        except pymysql.Error as e:
            logger.error(f"❌ Ошибка при добавлении стандартного вопроса: {str(e)}")
            return None
    
    def insert_question_variant(self, variant_text, embedding, std_question_id):
        """Добавляет вариант вопроса"""
        if not self.connection:
            return False
            
        try:
            with self.connection.cursor() as cursor:
                # Проверка на дубликат
                check_query = """
                SELECT id FROM question_variants 
                WHERE variant_text = %s AND standard_question_id = %s
                """
                cursor.execute(check_query, (variant_text, std_question_id))
                if cursor.fetchone():
                    return False  # Дубликат существует
                
                # Вставка нового варианта
                insert_query = """
                INSERT INTO question_variants 
                (variant_text, embedding, standard_question_id)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (variant_text, embedding, std_question_id))
                self.connection.commit()
                return True
        except pymysql.Error as e:
            logger.error(f"❌ Ошибка при добавлении варианта вопроса: {str(e)}")
            return False
    
    def find_closest_question(self, embedding):
        """Находит ближайший вопрос по эмбеддингу"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                # Получаем все варианты вопросов с эмбеддингами
                cursor.execute("""
                    SELECT qv.id, qv.embedding, qv.variant_text, 
                        sq.id AS std_question_id, sq.answer_id, sq.intent
                    FROM question_variants qv
                    JOIN standard_questions sq ON qv.standard_question_id = sq.id
                """)
                all_variants = cursor.fetchall()
                
                # Если нет вариантов, возвращаем None
                if not all_variants:
                    return None
                
                # Конвертируем BLOB в массивы numpy с явным указанием размера
                variant_embeddings = []
                valid_variants = []
                expected_size = 384 * 4  # 384 значения * 4 байта (float32)
                
                for variant in all_variants:
                    blob_data = variant['embedding']
                    
                    # Проверяем размер данных
                    if len(blob_data) != expected_size:
                        logger.warning(f"Некорректный размер эмбеддинга: {len(blob_data)} байт (ожидалось {expected_size})")
                        continue
                    
                    try:
                        array = np.frombuffer(blob_data, dtype=np.float32)
                        if array.shape[0] == 384:  # Проверяем размерность
                            variant_embeddings.append(array)
                            valid_variants.append(variant)
                    except Exception as e:
                        logger.error(f"Ошибка конвертации BLOB: {str(e)}")
                
                # Если после фильтрации не осталось валидных вариантов
                if not variant_embeddings:
                    return None
                
                # Рассчитываем косинусную схожесть
                from sklearn.metrics.pairwise import cosine_similarity
                similarities = cosine_similarity([embedding], variant_embeddings)[0]
                
                # Находим максимальную схожесть
                max_index = np.argmax(similarities)
                max_similarity = similarities[max_index]
                best_variant = valid_variants[max_index]
                
                return {
                    'variant_id': best_variant['id'],
                    'std_question_id': best_variant['std_question_id'],
                    'answer_id': best_variant['answer_id'],
                    'intent': best_variant['intent'],
                    'similarity': float(max_similarity),
                    'variant_text': best_variant['variant_text']
                }
        except Exception as e:
            logger.error(f"Ошибка поиска похожего вопроса: {str(e)}")
            return None
        
    def get_answer_text(self, answer_id):
        """Возвращает текст ответа по ID"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT answer_text FROM answers WHERE id = %s"
                cursor.execute(query, (answer_id,))
                result = cursor.fetchone()
                return result['answer_text'] if result else None
        except pymysql.Error as e:
            logger.error(f"Ошибка получения ответа: {str(e)}")
            return None
    
    # Методы для логирования
    def log_user_question(self, session_id, client_id, raw_question, 
                         normalized_text, embedding, standard_question_id=None,
                         answer_id=None, is_found=False, confidence=None,
                         response_time_ms=None):
        """Логирует вопрос пользователя в базу"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = """
                INSERT INTO user_questions (
                    session_id, client_id, raw_question, normalized_text, embedding,
                    standard_question_id, answer_id, is_found, confidence, response_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id, client_id or None, raw_question, normalized_text, embedding,
                    standard_question_id, answer_id, is_found, confidence, response_time_ms
                ))
                self.connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка при логировании вопроса: {str(e)}")
            return None
    
    def log_pending_question(self, user_question_id):
        """Добавляет вопрос в таблицу неотвеченных"""
        if not self.connection:
            return None
            
        try:
            with self.connection.cursor() as cursor:
                query = "INSERT INTO pending_questions (user_question_id) VALUES (%s)"
                cursor.execute(query, (user_question_id,))
                self.connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка при добавлении в pending_questions: {str(e)}")
            return None