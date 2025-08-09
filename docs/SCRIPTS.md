load_data.py
Загружает данные из CSV-файла в базу.
bash
python scripts/load_data.py --file base_qu_an/qu_ans_1.csv --header


add_question.py
Добавляет один вопрос в базу данных.
bash
python scripts/add_question.py --question "Как стать волонтером?" --answer "Заполните форму на нашем сайте" --intent "volunteering"


view_pending.py
Просмотр необработанных вопросов.
bash
python scripts/view_pending.py

process_pending.py
Обработка неотвеченных вопросов.
bash
python scripts/process_pending.py --id 5 --answer "Ответ на вопрос" --intent "new_intent"