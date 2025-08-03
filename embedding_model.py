import re
import logging
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_path):
        logger.info(f"Загружаем модель из {model_path}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModel.from_pretrained(model_path)
            logger.info("Модель успешно загружена")
        except Exception as e:
            logger.critical(f"Ошибка загрузки модели: {str(e)}")
            raise
        
        self.stop_words = {
            "и", "в", "с", "на", "но", "а", "о", "у", "к", "я", "ты", "мы", 
            "что", "как", "для", "по", "из", "от", "же", "за", "вы", "со", "то",
            "мне", "все", "его", "ее", "их", "они", "оно", "это", "так", "тут"
        }
    
    def normalize_text(self, text):
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        words = text.split()
        return ' '.join(words)
        
    def get_embedding(self, text):
        normalized = self.normalize_text(text)
        
        # Токенизация и получение эмбеддингов
        inputs = self.tokenizer(normalized, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Усреднение эмбеддингов последнего слоя
        embeddings = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        masked_embeddings = embeddings * mask
        summed = torch.sum(masked_embeddings, 1)
        summed_mask = torch.clamp(mask.sum(1), min=1e-9)
        mean_pooled = summed / summed_mask
        
        # Нормализация
        normalized_embedding = F.normalize(mean_pooled, p=2, dim=1)
        return normalized_embedding[0].numpy()