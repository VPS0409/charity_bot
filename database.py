# database.py

import pymysql
import logging
import numpy as np
import config
from utils import blob_to_array
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self):
        logger.info(f"Попытка подключения к БД: {self.user}@{self.host}/{self.database}")
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("Подключение к БД успешно установлено")
            return True
        except pymysql.Error as e:
            error_code = e.args[0] if e.args else 'N/A'
            error_msg = e.args[1] if len(e.args) > 1 else str(e)
            logger.error(f"Ошибка подключения к БД (код {error_code}): {error_msg}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при подключении: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
                logger.info("Отключено от БД")
            except Exception as e:
                logger.error(f"Ошибка при отключении: {e}")
        self.connection = None
    
    def get_cursor(self):
        """Создает и возвращает курсор с обработкой ошибок"""
        if not self.connection or not self.connection.open:
            if not self.connect():
                return None
            
        try:
            return self.connection.cursor()
        except pymysql.Error as e:
            logger.error(f"Ошибка создания курсора: {e}")
            return None
    
    def execute_query(self, query, params=None, commit=False):
        """Выполняет SQL-запрос и возвращает результат"""
        cursor = self.get_cursor()
        if not cursor:
            return None
            
        try:
            cursor.execute(query, params or ())
            if commit:
                self.connection.commit()
            return cursor
        except pymysql.Error as e:
            logger.error(f"Ошибка выполнения запроса: {str(e)}")
            return None
    
    def find_closest_question(self, embedding):
        """Ищем ближайший вопрос в базе данных"""
        cursor = self.execute_query("SELECT id, embedding, intent FROM questions")
        if not cursor:
            logger.error("Нет подключения к БД для поиска вопроса")
            return None
            
        try:
            min_dist = float('inf')
            closest_id = None
            closest_intent = None
            
            for row in cursor:
                q_id = row['id']
                emb_blob = row['embedding']
                intent = row['intent']
                
                # Пропускаем пустые значения
                if emb_blob is None:
                    logger.warning(f"Пустой BLOB для вопроса id={q_id}")
                    continue
                    
                try:
                    # Преобразуем BLOB в массив numpy
                    db_embedding = blob_to_array(emb_blob)
                    
                    # Рассчитываем косинусное расстояние
                    dist = self.cosine_distance(embedding, db_embedding)
                    
                    if dist < min_dist:
                        min_dist = dist
                        closest_id = q_id
                        closest_intent = intent
                except Exception as e:
                    logger.error(f"Ошибка обработки эмбеддинга для вопроса id={q_id}: {str(e)}")
                    continue
                    
            if closest_id is None:
                logger.info("Не найдено подходящих вопросов")
                return None
            
            logger.info(f"Найден ближайший вопрос: id={closest_id}, distance={min_dist:.4f}, intent={closest_intent}")
            similarity = 1 - min_dist
            return closest_id, similarity, closest_intent
            
        except Exception as e:
            logger.error(f"Общая ошибка при поиске ближайшего вопроса: {str(e)}")
            return None
        finally:
            cursor.close()

    def cosine_distance(self, vec1, vec2):
        """Вычисляем косинусное расстояние между двумя векторами"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Избегаем деления на ноль
            if norm1 == 0 or norm2 == 0:
                logger.warning("Нулевая норма вектора")
                return 1.0
                
            cosine_sim = dot_product / (norm1 * norm2)
            return 1 - cosine_sim
        except Exception as e:
            logger.error(f"Ошибка в cosine_distance: {str(e)}")
            return 1.0
    
    def get_question_answer(self, question_id):
        """Получаем текст ответа из таблицы answers"""
        cursor = self.execute_query(
            "SELECT a.answer_text "
            "FROM questions q "
            "JOIN answers a ON q.answer_id = a.id "
            "WHERE q.id = %s",
            (question_id,)
        )
        
        if not cursor:
            logger.error("Ошибка выполнения запроса ответа")
            return None
            
        result = cursor.fetchone()
        cursor.close()
    
        return result['answer_text'] if result else None
            
    def save_pending_question(self, original_question, normalized_question, embedding_blob):
        """Сохраняет неотвеченный вопрос в таблицу pending_questions"""
        cursor = self.execute_query(
            "INSERT INTO pending_questions (original_text, normalized_text, embedding) VALUES (%s, %s, %s)",
            (original_question, normalized_question, embedding_blob),
            commit=True
        )
        if cursor:
            cursor.close()
            return True
        return False
    
    def question_exists(self, question_text):
        """Проверяет, существует ли уже такой вопрос в базе"""
        cursor = self.execute_query(
            "SELECT COUNT(*) AS cnt FROM questions WHERE question_text = %s",
            (question_text,)
        )
        if cursor:
            result = cursor.fetchone()
            cursor.close()
            return result['cnt'] > 0 if result else False
        return False

    def insert_answer(self, answer_text):
        """Добавляет новый ответ в таблицу answers и возвращает его ID"""
        cursor = self.execute_query(
            "INSERT INTO answers (answer_text) VALUES (%s)",
            (answer_text,),
            commit=True
        )
        if cursor:
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        return None

    def insert_question(self, question_text, answer_id, embedding, intent):
        """Добавляет новый вопрос в таблицу questions"""
        cursor = self.execute_query(
            "INSERT INTO questions (question_text, answer_id, embedding, intent) VALUES (%s, %s, %s, %s)",
            (question_text, answer_id, embedding, intent),
            commit=True
        )
        if cursor:
            cursor.close()
            return True
        return False
    
      