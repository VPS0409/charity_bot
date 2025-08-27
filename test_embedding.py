#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath('.'))

from embedding_model import EmbeddingModel
import config

def test_embedding():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ ЭМБЕДДИНГОВ")
    print("=" * 60)
    
    try:
        # Инициализация модели
        embedder = EmbeddingModel(config.MODEL_PATH)
        print("✓ Модель успешно загружена")
        
        # Тестовый вопрос
        test_question = "Я записался к психиатру через хоспис, что дальше?"
        print(f"Тестовый вопрос: {test_question}")
        
        # Нормализация
        normalized = embedder.normalize_text(test_question)
        print(f"Нормализованный вопрос: {normalized}")
        
        # Эмбеддинг
        embedding = embedder.get_embedding(normalized)
        print(f"Размер эмбеддинга: {len(embedding)}")
        print(f"Первые 5 значений эмбеддинга: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при работе с моделью: {e}")
        return False

if __name__ == "__main__":
    test_embedding()