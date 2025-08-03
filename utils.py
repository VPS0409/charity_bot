# Файл utils.py
# Вспомогательные утилиты

import numpy as np

def blob_to_array(blob):
    """Преобразует BLOB из базы данных в массив numpy"""
    return np.frombuffer(blob, dtype=np.float32)

def array_to_blob(array):
    """Преобразует массив numpy в BLOB для сохранения в базе"""
    return array.tobytes()