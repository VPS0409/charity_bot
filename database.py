# database.py
import pymysql
import logging
import numpy as np
from datetime import datetime
import traceback 
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def _get_connection(self):
        """Создает и возвращает новое соединение с базой данных"""
        try:
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            self.connection = conn
            return conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return None

    def execute_query(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            return None
        finally:
            conn.close()

    def execute_update(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            return False
        finally:
            conn.close()

    def get_question_groups(self):
        return self.execute_query("SELECT id, name FROM questions_groups")

    def get_all_standard_questions(self):
        return self.execute_query("""
            SELECT id, group_id, title, answer_id, intent 
            FROM standard_questions
        """)

    def get_all_answers(self):
        results = self.execute_query("SELECT id, answer_text FROM answers")
        if not results:
            return []
        return [{'id': row['id'], 'text': row['answer_text']} for row in results]

    # -------------------- РАБОЧАЯ ВЕРСИЯ поиска ближайшего вопроса --------------------
    def find_closest_question(self, embedding):
        """Находит ближайший вопрос по эмбеддингу"""
        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT qv.id, qv.embedding, qv.variant_text, 
                           sq.id AS std_question_id, sq.answer_id, sq.intent
                    FROM question_variants qv
                    JOIN standard_questions sq ON qv.standard_question_id = sq.id
                """)
                all_variants = cursor.fetchall()

                if not all_variants:
                    return None

                variant_embeddings = []
                valid_variants = []
                expected_size = 384 * 4  # 384 значений * 4 байта (float32)

                for variant in all_variants:
                    blob_data = variant['embedding']
                    if len(blob_data) != expected_size:
                        logger.warning(
                            f"Некорректный размер эмбеддинга: {len(blob_data)} байт (ожидалось {expected_size})"
                        )
                        continue
                    try:
                        array = np.frombuffer(blob_data, dtype=np.float32)
                        if array.shape[0] == 384:
                            variant_embeddings.append(array)
                            valid_variants.append(variant)
                    except Exception as e:
                        logger.error(f"Ошибка конвертации BLOB: {str(e)}")

                if not variant_embeddings:
                    return None

                similarities = cosine_similarity([embedding], variant_embeddings)[0]
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
            logger.error(traceback.format_exc())
            return None
        finally:
            conn.close()

    def get_answer_text(self, answer_id):
        """Возвращает текст ответа по ID"""
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                query = "SELECT answer_text FROM answers WHERE id = %s"
                cursor.execute(query, (answer_id,))
                result = cursor.fetchone()
                return result['answer_text'] if result else None
        except pymysql.Error as e:
            logger.error(f"Ошибка получения ответа: {str(e)}")
            return None
        finally:
            conn.close()

    def insert_group(self, name):
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO questions_groups (name) VALUES (%s)", (name,))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка создания группы: {e}")
            return None
        finally:
            conn.close()

    def insert_answer(self, answer_text):
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO answers (answer_text) VALUES (%s)", (answer_text,))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка создания ответа: {e}")
            return None
        finally:
            conn.close()

    def insert_standard_question(self, title, group_id, answer_id, intent):
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO standard_questions (title, group_id, answer_id, intent)
                    VALUES (%s, %s, %s, %s)
                """, (title, group_id, answer_id, intent))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка создания стандартного вопроса: {e}")
            return None
        finally:
            conn.close()

    def insert_question_variant(self, variant_text, embedding, standard_question_id):
        conn = self._get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO question_variants (variant_text, embedding, standard_question_id)
                    VALUES (%s, %s, %s)
                """, (variant_text, embedding, standard_question_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания варианта вопроса: {e}")
            return False
        finally:
            conn.close()

    def log_user_question(self, session_id, client_id, raw_question, normalized_text, 
                        embedding, is_found, response_time_ms, standard_question_id=None, 
                        answer_id=None, confidence=None):
        """Логирует вопрос пользователя в базу данных"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO user_questions 
                    (session_id, client_id, raw_question, normalized_text, embedding, 
                    standard_question_id, answer_id, is_found, confidence, response_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id, client_id, raw_question, normalized_text, embedding,
                    standard_question_id, answer_id, is_found, confidence, response_time_ms
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка логирования вопроса пользователя: {e}")
            return None
        finally:
            conn.close()

    def log_pending_question(self, question_id):
        """Добавляет вопрос в таблицу pending_questions для последующей обработки"""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Получаем данные вопроса из user_questions
                cursor.execute("""
                    SELECT original_text, normalized_text, embedding 
                    FROM user_questions WHERE id = %s
                """, (question_id,))
                question_data = cursor.fetchone()
                
                if not question_data:
                    return False
                
                # Вставляем в pending_questions
                cursor.execute("""
                    INSERT INTO pending_questions (original_text, normalized_text, embedding)
                    VALUES (%s, %s, %s)
                """, (question_data['raw_question'], question_data['normalized_text'], question_data['embedding']))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления вопроса в ожидание: {e}")
            return False
        finally:
            conn.close()
