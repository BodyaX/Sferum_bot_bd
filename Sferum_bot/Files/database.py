import sqlite3
import os
from fastapi import FastAPI

storage = 'Files'
os.makedirs(storage, exist_ok=True) # Создаем папку, если ее нет

# Подключаемся к бд и создаем таблицу для метаданных.
db = sqlite3.connect('my_bot.db')
sql = db.cursor()
sql.execute("""
create table if not exists files ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT
    name TEXT,
    file_path TEXT,
    uid TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
db.commit()
db.close() 

#запуск сервера
app = FastAPI(title="Server")

# Функция  срабатывает, когда бот или клиент шлет пост запрос 
@app.post("/upload/")
def upload_file(request_data: dict):
    user_id = request_data["uid"]

    # Вырезаем слеши из имени и расширения, защита от атаки
    file_name = request_data["name"].replace("/", "").replace("\\", "")
    file_ext = request_data["extension"].replace("/", "").replace("\\", "")
    file_content = request_data["data"]

    # Склеиваем безопасное имя и путь
    full_file_name = f"{file_name}.{file_ext}"
    file_path = f"{storage}/{full_file_name}"
    
    # Открываем файл для записи
    # with - безопасно закроет файл в конце
    # utf-8 - чтобы русские буквы из конспекта не стали иероглифами
    with open(file_path, "w", encoding="utf-8") as buffer:
        buffer.write(file_content) #закрытие диска
        
    # Конструкция with сама откроет базу, сама сделает commit при успехе и сама её закроет
    with sqlite3.connect('my_bot.db') as local_db:
        # Записываем данные в таблицу.
        # Это защита от SQL-инъекций (чтобы хакер не смог удалить таблицу через имя файла)
        local_db.execute(
            "INSERT INTO files (name, extension, uid, file_path) VALUES (?, ?, ?, ?)", 
            (full_file_name, file_ext, user_id, file_path)
        )
        
    return {"status": "success", "message": f"Конспект {full_file_name} успешно сохранен!"}