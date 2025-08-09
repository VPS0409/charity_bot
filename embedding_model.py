# Файл embedding_model.py
import numpy as np  # Добавляем импорт numpy
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_path: str):
        try:
            logger.info(f"Загрузка модели из {model_path}")
            self.model = SentenceTransformer(model_path)
            logger.info("Модель успешно загружена")
        except Exception as e:
            logger.exception(f"Ошибка загрузки модели: {str(e)}")
            raise RuntimeError(f"Не удалось загрузить модель") from e
    
    def normalize_text(self, text: str) -> str:
        """Нормализует текст: приводит к нижнему регистру и удаляет лишние пробелы"""
        return text.lower().strip()
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Возвращает эмбеддинг для текста"""
        return self.model.encode([text])[0]