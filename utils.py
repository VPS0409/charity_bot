# Файл utils.py
# utils.py
import numpy as np
import pickle

def array_to_blob(arr: np.ndarray) -> bytes:
    """Преобразует массив numpy в бинарный объект для хранения в БД"""
    return pickle.dumps(arr, protocol=pickle.HIGHEST_PROTOCOL)

def blob_to_array(blob: bytes) -> np.ndarray:
    """Преобразует бинарный объект из БД в массив numpy"""
    return pickle.loads(blob)