# Файл app.py
import os
from dotenv import load_dotenv
import time
from flask import Flask, request, jsonify, session
import secrets
import traceback  # Добавьте эту строку
import logging
import signal
import sys

# Загрузка переменных окружения ПЕРВЫМ делом
load_dotenv()

# Теперь импортируем config, который будет использовать загруженные переменные
import config

# Остальные импорты
os.environ["TOKENIZERS_PARALLELISM"] = "false" if not config.DEBUG else "true"
from database import Database
from embedding_model import EmbeddingModel
from utils import array_to_blob
import logging
import signal
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Инициализация базы данных и модели
logger.info("Инициализация подключения к БД...")
db = Database(
    config.DB_HOST, 
    config.DB_USER, 
    config.DB_PASSWORD, 
    config.DB_NAME
)
embedder = EmbeddingModel(config.MODEL_PATH)

# Обработчики для корректного завершения работы
def handle_exit(signum, frame):
    logger.info("\nСервер завершает работу...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Разрешаем CORS для всех доменов
@app.after_request
def add_cors_headers(response):
    """Добавляет CORS заголовки ко всем ответам"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# Специальный обработчик для OPTIONS-запросов
@app.route('/api/groups', methods=['OPTIONS'])
@app.route('/api/questions', methods=['OPTIONS'])
@app.route('/api/answers', methods=['OPTIONS'])
@app.route('/api/ask', methods=['OPTIONS'])
@app.route('/test_similarity', methods=['OPTIONS'])
def handle_options():
    """Обрабатывает OPTIONS-запросы для CORS"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return "Сервер чатбота для благотворительного фонда работает!"

# Новые эндпоинты для фронтенда
@app.route('/api/groups', methods=['GET'])
def api_groups():
    """Возвращает список групп вопросов"""
    try:
        groups = db.get_question_groups()
        return jsonify(groups)
    except Exception as e:
        logger.exception("Ошибка при получении групп вопросов")
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions', methods=['GET'])
def api_questions():
    """Возвращает все стандартные вопросы"""
    try:
        questions = db.get_all_standard_questions()
        return jsonify(questions)
    except Exception as e:
        logger.exception("Ошибка при получении стандартных вопросов")
        return jsonify({"error": str(e)}), 500

@app.route('/api/answers', methods=['GET'])
def api_answers():
    """Возвращает все ответы"""
    try:
        answers = db.get_all_answers()
        return jsonify(answers)
    except Exception as e:
        logger.exception("Ошибка при получении ответов")
        return jsonify({"error": str(e)}), 500

# Основной эндпоинт для обработки вопросов
@app.route('/api/ask', methods=['POST', 'GET'])
def handle_question():
    logger.info(f"Получен запрос {request.method} на /api/ask")
    
    # Если это GET-запрос, возвращаем информацию об эндпоинте
    if request.method == 'GET':
        logger.info("Обработка GET-запроса на /api/ask")
        return jsonify({
            "message": "Этот эндпоинт предназначен для обработки вопросов через POST-запросы",
            "example_request": {
                "method": "POST",
                "url": "/api/ask",
                "body": {"question": "Ваш вопрос здесь"}
            }
        })
    
    # Обработка POST-запроса
    logger.info("Обработка POST-запроса на /api/ask")
    start_time = time.time()
    try:
        # Получаем идентификатор сессии
        session_id = session.get('session_id', 'unknown')
        client_id = request.headers.get('X-Client-ID', 'unknown')
        
        # Проверяем JSON
        if not request.is_json:
            logger.error("Отсутствует тело запроса в формате JSON")
            return jsonify({"error": "Missing JSON body"}), 400
            
        data = request.get_json()
        original_question = data.get('question', '')
        if not original_question:
            return jsonify({"error": "Missing 'question' field"}), 400
        
        logger.info(f"Обработка вопроса: '{original_question}' от сессии {session_id}")
        
        # Нормализуем вопрос
        normalized_question = embedder.normalize_text(original_question)
        
        # Рассчитываем эмбеддинг
        embedding = embedder.get_embedding(normalized_question)
        embedding_blob = array_to_blob(embedding)
        
        # Ищем ближайший вопрос в базе
        result = db.find_closest_question(embedding)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Если не найдено или низкая уверенность
        if not result or result.get('similarity', 0) < config.SIMILARITY_THRESHOLD:
            # Логируем неотвеченный вопрос
            # question_id = db.log_user_question(
            #     session_id=session_id,
            #     client_id=client_id,
            #     raw_question=original_question,
            #     normalized_text=normalized_question,
            #     embedding=embedding_blob,
            #     is_found=False,
            #     response_time_ms=response_time_ms
            # )
            
            # if question_id:
            #     db.log_pending_question(question_id)
            #     logger.info(f"Вопрос добавлен в ожидание обработки, ID: {question_id}")
            
            return jsonify({
                "answer": "Извините, я не нашел ответ на ваш вопрос. Наш специалист свяжется с вами в ближайшее время.",
                "intent": "unknown",
                "confidence": result.get('similarity', 0) if result else 0
            })
        
        # Извлекаем данные из результата
        similarity = result['similarity']
        answer_id = result['answer_id']
        intent = result['intent']
        matched_question = result.get('variant_text', '')
        
        logger.info(f"Найден похожий вопрос: '{matched_question}' с уверенностью {similarity:.2f}")
        
        # Получаем текст ответа
        answer_text = db.get_answer_text(answer_id)
        if not answer_text:
            # Логируем как неотвеченный
            question_id = db.log_user_question(
                session_id=session_id,
                client_id=client_id,
                raw_question=original_question,
                normalized_text=normalized_question,
                embedding=embedding_blob,
                is_found=False,
                response_time_ms=response_time_ms
            )
            
            # if question_id:
            #     db.log_pending_question(question_id)
            
            return jsonify({
                "answer": "Извините, я не нашел ответ на ваш вопрос. Наш специалист свяжется с вами в ближайшее время.",
                "intent": "unknown",
                "confidence": similarity
            })
        
        # Логируем успешный ответ
        # db.log_user_question(
        #     session_id=session_id,
        #     client_id=client_id,
        #     raw_question=original_question,
        #     normalized_text=normalized_question,
        #     embedding=embedding_blob,
        #     standard_question_id=result['standard_question_id'],
        #     answer_id=answer_id,
        #     is_found=True,
        #     confidence=similarity,
        #     response_time_ms=response_time_ms
        # )
        
        logger.info(f"Вопрос успешно обработан, ответ ID: {answer_id}")
        
        return jsonify({
            "answer": answer_text,
            "intent": intent,
            "confidence": similarity,
            "followup": []  # Можно добавить уточняющие вопросы при необходимости
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
            
        return jsonify({
            "input_question": test_question,
            "matched_question": result.get('variant_text', ''),
            "similarity": result['similarity'],
            "similarity_threshold": config.SIMILARITY_THRESHOLD
        })
        
    except Exception as e:
        logger.exception("Ошибка в тестовом эндпоинте")
        return jsonify({"error": str(e)}), 500
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
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

app.secret_key = secrets.token_hex(16)  # Генерация секретного ключа
