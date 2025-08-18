# Файл utils.py
import numpy as np
import logging

logger = logging.getLogger(__name__)

def array_to_blob(array):
    """Конвертирует numpy array в бинарный формат для БД"""
    try:
        return array.tobytes()
    except Exception as e:
        logger.error(f"Ошибка конвертации массива в BLOB: {str(e)}")
        return None

def blob_to_array(blob):
    """Конвертирует бинарные данные из БД в numpy array"""
    try:
        return np.frombuffer(blob, dtype=np.float32)
    except Exception as e:
        logger.error(f"Ошибка конвертации BLOB в массив: {str(e)}")
        return None