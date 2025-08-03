# Файл database.py
# Функции работы с MySQL

import mysql.connector
import numpy as np
from utils import blob_to_array
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None
        
    def connect(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                logger.info("Подключение к БД успешно установлено")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            return False
            
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            try:
                # Закрываем все открытые курсоры
                while self.connection.unread_result:
                    self.connection.cmd_query_reset()
                
                self.connection.close()
                logger.info("Соединение с БД закрыто")
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения: {str(e)}")
    
    def execute_query(self, query, params=None):
        """Выполняет SQL-запрос и возвращает результат"""
        if not self.connect():
            return None
            
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except mysql.connector.Error as e:
            logger.error(f"Ошибка выполнения запроса: {str(e)}")
            return None
    
    def question_exists(self, question_text):
        """Проверяет, существует ли уже такой вопрос в базе"""
        cursor = self.execute_query(
            "SELECT COUNT(*) FROM questions WHERE question_text = %s",
            (question_text,)
        )
        if cursor:
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0 if result else False
        return False
    
    def find_closest_question(self, embedding):
        """Ищем ближайший вопрос в базе данных"""
        if not self.connect():
            logger.error("Нет подключения к БД для поиска вопроса")
            return None
            # return closest_id, 1 - min_dist, closest_intent 
            
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("SELECT COUNT(*) FROM questions")
            count = cursor.fetchone()[0]
            logger.info(f"Найдено вопросов в базе: {count}")
            cursor.execute("SELECT id, embedding, intent FROM questions")
            min_dist = float('inf')
            closest_id = None
            closest_intent = None
            
            # Получаем все результаты сразу
            rows = cursor.fetchall()
            for (q_id, emb_blob, intent) in rows:
                # Преобразуем BLOB в массив numpy
                db_embedding = blob_to_array(emb_blob)
                
                # Рассчитываем косинусное расстояние
                dist = self.cosine_distance(embedding, db_embedding)
                
                if dist < min_dist:
                    min_dist = dist
                    closest_id = q_id
                    closest_intent = intent
                    
            cursor.close()
            if closest_id is None:
                logger.info("Не найдено подходящих вопросов")
                return None
            
            if closest_id:
                logger.info(f"Найден ближайший вопрос: id={closest_id}, distance={min_dist:.4f}, intent={closest_intent}")
                similarity = 1 - min_dist
                return closest_id, similarity, closest_intent

                
            logger.info("Не найдено ни одного вопроса в базе")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске ближайшего вопроса: {str(e)}")
            return None
            
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
        cursor = self.execute_query(
        "SELECT a.answer_text FROM answers a JOIN questions q ON a.id = q.answer_id WHERE q.id = %s",
        (question_id,)
    )
    
        if cursor is None:
            logger.error("Ошибка выполнения запроса ответа")
            return None
            
        result = cursor.fetchone()
        cursor.close()
    
        return result[0] if result else None
            
    def save_pending_question(self, original_question, normalized_question, embedding_blob):
        """Сохраняет неотвеченный вопрос в таблицу pending_questions"""
        cursor = self.execute_query(
            "INSERT INTO pending_questions (original_question, normalized_question, embedding) VALUES (%s, %s, %s)",
            (original_question, normalized_question, embedding_blob)
        )
        if cursor:
            cursor.close()
            return True
        return False