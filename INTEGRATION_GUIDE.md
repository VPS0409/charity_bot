Инструкции для разработчиков по подключению и использованию API

**Репозиторий проекта**:  
https://github.com/VPS0409/charity_bot

📚 **Документация**:  
Полная инструкция по установке в файле [README.md](https://github.com/VPS0409/charity_bot/blob/main/README.md)

🛠 **Как начать работу:**
1. Склонируйте репозиторий:  
   `git clone https://github.com/VPS0409/charity_bot.git`
2. Следуйте инструкциям в README.md
3. Для интеграции с сайтом используйте API эндпоинт:  
   `POST /api/ask`

🔧 **Технические детали интеграции:**
```javascript
// Пример запроса с фронтенда
async function askBot(question) {
  const response = await fetch('https://ваш-домен/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  return await response.json();
}

// Пример использования
askBot("Как получить лекарства?").then(data => {
  if(data.status === 'success') {
    console.log("Ответ:", data.answer);
  } else {
    console.log("Неизвестный вопрос");
  }
});
📬 Важные заметки:

ML-модель требует отдельной загрузки (инструкция в README)

Для работы требуется MySQL

Конфигурация через .env файл

Готовые Docker-образы будут доступны позже

💬 Вопросы и предложения:

Задачи и баги: Issues

Обсуждение интеграции: Slack/email/Teams