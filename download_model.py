# download_model.py
from sentence_transformers import SentenceTransformer
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_PATH = "models/all-MiniLM-L6-v2"

def download_model():
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH, exist_ok=True)
        logger.info(f"Загрузка модели {MODEL_NAME}...")
        
        try:
            model = SentenceTransformer(MODEL_NAME)
            model.save(MODEL_PATH)
            logger.info(f"Модель успешно загружена и сохранена в {MODEL_PATH}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False
    else:
        logger.info(f"Модель уже загружена в {MODEL_PATH}")
        return True

if __name__ == "__main__":
    download_model()