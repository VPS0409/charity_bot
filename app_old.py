# app.py
import os
from dotenv import load_dotenv

# Загрузка переменных окружения ПЕРВЫМ делом
load_dotenv()

# Теперь импортируем config, который будет использовать загруженные переменные
import config

# Остальные импорты
os.environ["TOKENIZERS_PARALLELISM"] = "false" if not config.DEBUG else "true"
from flask import Flask, request, jsonify
from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob
from datetime import datetime
import logging
import signal
import sys

# ... остальной код без изменений ...

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Диагностика
logger.info(f"Текущая рабочая директория: {os.getcwd()}")
logger.info(f"Абсолютный путь к модели: {os.path.abspath(config.MODEL_PATH)}")
logger.info(f"Существует ли директория: {os.path.exists(config.MODEL_PATH)}")

if os.path.exists(config.MODEL_PATH):
    logger.info(f"Файлы в директории: {os.listdir(config.MODEL_PATH)}")
else:
    logger.error("Директория не существует!")

app = Flask(__name__)

# Инициализация базы данных и модели
logger.info("Инициализация подключения к БД...")
db = Database(
    config.DB_HOST, 
    config.DB_USER, 
    config.DB_PASSWORD, 
    config.DB_NAME
)

# Проверка подключения при запуске
logger.info("Проверка подключения к БД...")
if db.connect():
    logger.info("Проверочное подключение к БД успешно")
    db.disconnect()
else:
    logger.error("Не удалось подключиться к БД при запуске!")

embedder = EmbeddingModel(config.MODEL_PATH)

# Обработчики для корректного завершения работы
def handle_exit(signum, frame):
    logger.info("\nСервер завершает работу...")
    db.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

@app.before_request
def before_request():
    if not db.connect():
        return jsonify({"error": "Database connection failed"}), 500

@app.teardown_request
def teardown_request(exception=None):
    db.disconnect()

@app.route('/')
def home():
    return "Сервер чатбота для благотворительного фонда работает!"

@app.route('/ask', methods=['POST'])
def handle_question():
    try:
        # Логируем получение запроса
        logger.info(f"\n{'='*50}\nПолучен запрос на /ask в {datetime.now()}")
        logger.info(f"Заголовки: {request.headers}")
        
        # Проверяем JSON
        if not request.is_json:
            logger.error("Отсутствует тело запроса в формате JSON")
            return jsonify({"error": "Missing JSON body"}), 400
            
        data = request.get_json()
        logger.info(f"Данные: {data}\n{'='*50}")
        
        if 'question' not in data:
            logger.error("В запросе отсутствует поле 'question'")
            return jsonify({"error": "Missing 'question' field"}), 400
            
        original_question = data['question']
        
        # Нормализуем вопрос
        normalized_question = embedder.normalize_text(original_question)
        logger.info(f"Нормализованный вопрос: {normalized_question}")
        
        # Рассчитываем эмбеддинг
        embedding = embedder.get_embedding(normalized_question)
        logger.info(f"Эмбеддинг рассчитан, размер: {len(embedding)}")
        
        # Ищем ближайший вопрос в базе
        result = db.find_closest_question(embedding)
        
        # Логируем результат поиска
        logger.info(f"Результат поиска: {result}")
        
        # Обработка случая, когда ничего не найдено
        if result is None:
            logger.info("Не найдено ни одного вопроса в базе данных")
            return jsonify({
                "answer": "Обратитесь к оператору или в офис",
                "intent": "unknown"
            })
            
        # Распаковываем результат
        q_id, similarity, intent = result
        logger.info(f"Найден кандидат: id={q_id}, сходство={similarity:.4f}, intent={intent}")
        logger.info(f"Порог сходства: {config.SIMILARITY_THRESHOLD}")
        
        # Проверяем, превышает ли сходство пороговое значение
        if similarity < config.SIMILARITY_THRESHOLD:
            logger.info(f"Сходство {similarity:.4f} < порога {config.SIMILARITY_THRESHOLD} - используем стандартный ответ")
            
            # Сохраняем вопрос для последующей обработки
            blob = array_to_blob(embedding)
            if db.save_pending_question(original_question, normalized_question, blob):
                logger.info("Вопрос сохранен для обработки оператором")
            else:
                logger.error("Ошибка при сохранении неотвеченного вопроса")
            
            return jsonify({
                "answer": "обратиться к оператору или в офис",
                "intent": "unknown"
            })
            
        # Если сходство выше порога - ищем ответ
        logger.info(f"Сходство {similarity:.4f} >= порога {config.SIMILARITY_THRESHOLD} - используем ответ из базы")
        answer_text = db.get_question_answer(q_id)
        
        if not answer_text:
            logger.error(f"Найден вопрос id={q_id}, но ответ отсутствует в базе")
            return jsonify({
                "answer": "обратиться к оператору или в офис",
                "intent": "unknown"
            })
        
        logger.info(f"Найден ответ: intent={intent}, confidence={similarity:.4f}")
        
        return jsonify({
            "answer": answer_text,
            "intent": intent,
            "confidence": float(similarity)
        })
        
    except Exception as ex:
        logger.exception("Критическая ошибка при обработке вопроса")
        return jsonify({
            "error": "Internal server error",
            "details": str(ex)
        }), 500

# Новый эндпоинт для тестирования схожести
@app.route('/test_similarity', methods=['GET'])
def test_similarity():
    """Тестовый эндпоинт для проверки работы системы"""
    try:
        test_question = "Кто может получить консультацию и сколько раз"
        
        # Нормализуем вопрос
        normalized = embedder.normalize_text(test_question)
        logger.info(f"Тестовый вопрос: '{test_question}'")
        logger.info(f"Нормализованный тестовый вопрос: '{normalized}'")
        
        # Рассчитываем эмбеддинг
        embedding = embedder.get_embedding(normalized)
        logger.info(f"Эмбеддинг рассчитан, размер: {len(embedding)}")
        
        # Ищем в базе
        result = db.find_closest_question(embedding)
        
        if not result:
            return jsonify({"error": "Question not found in database"}), 404
            
        q_id, similarity, intent = result
        
        # Получаем текст вопроса из базы
        if not db.connect():
            return jsonify({"error": "Database connection failed"}), 500
            
        with db.connection.cursor() as cursor:
            cursor.execute(
                "SELECT question_text FROM questions WHERE id = %s",
                (q_id,)
            )
            db_question = cursor.fetchone()
            if not db_question:
                return jsonify({"error": "Database record not found"}), 404
                
            db_question_text = db_question['question_text']
        
        return jsonify({
            "input_question": test_question,
            "db_question": db_question_text,
            "normalized_input": normalized,
            "similarity": similarity,
            "similarity_threshold": config.SIMILARITY_THRESHOLD
        })
        
    except Exception as e:
        logger.exception("Ошибка в тестовом эндпоинте")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    logger.info(f"Запуск сервера на порту {config.PORT}...")
    logger.info(f"Режим отладки: {'ВКЛ' if config.DEBUG else 'ВЫКЛ'}")
    
    run_simple(
        hostname='0.0.0.0', 
        port=config.PORT, 
        application=app,
        use_reloader=config.DEBUG,
        use_debugger=config.DEBUG,
        threaded=True
    )