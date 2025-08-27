#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath('.'))

from database import Database
from embedding_model import EmbeddingModel
import config

def test_search():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ПОИСКА ПОХОЖИХ ВОПРОСОВ")
    print("=" * 60)
    
    try:
        # Инициализация
        db = Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
        embedder = EmbeddingModel(config.MODEL_PATH)
        
        test_question = "Я записался к психиатру через хоспис, что дальше?"
        print(f"Тестовый вопрос: {test_question}")
        
        # Получаем эмбеддинг
        normalized = embedder.normalize_text(test_question)
        embedding = embedder.get_embedding(normalized)
        
        # Ищем похожий вопрос
        result = db.find_closest_question(embedding)
        
        if result:
            print("✓ Найден похожий вопрос:")
            print(f"  ID стандартного вопроса: {result.get('std_question_id')}")
            print(f"  Заголовок: {result.get('title')}")
            print(f"  ID ответа: {result.get('answer_id')}")
            print(f"  Intent: {result.get('intent')}")
            print(f"  Вариант текста: {result.get('variant_text')}")
            print(f"  Уверенность: {result.get('similarity', 0):.4f}")
            
            # Получаем текст ответа
            if result.get('answer_id'):
                answer_text = db.get_answer_text(result['answer_id'])
                print(f"  Текст ответа: {answer_text}")
        else:
            print("✗ Похожих вопросов не найдено")
            
    except Exception as e:
        print(f"✗ Ошибка при поиске: {e}")

if __name__ == "__main__":
    test_search()