import sqlite3
import os
from fastapi import FastAPI

storage = 'Files'
os.makedirs(storage, exist_ok=True) # Создаем папку, если ее нет

# Настройка бд
db = sqlite3.connect('my_bot.db')
sql = db.cursor()
sql.execute("""
create table if not exists files ( 
    name TEXT,
    file_path TEXT,
    uid TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
db.commit()
db.close() 

#создаем сервер
app = FastAPI(title="Server")

@app.post("/upload/")
def upload_file(request_data: dict):
    user_id = request_data["uid"]
    file_name = request_data["name"]
    file_ext = request_data["extension"]
    file_content = request_data["data"]
    
    full_file_name = f"{file_name}.{file_ext}"
    file_path = f"{storage}/{full_file_name}"
    
    # 1. Сохраняем файл на диск
    with open(file_path, "w", encoding="utf-8") as buffer:
        buffer.write(file_content)
        
    # 2. Пишем в базу данных (ВНУТРИ ФУНКЦИИ!)
    # Конструкция with сама откроет базу, сама сделает commit при успехе и сама её закроет
    with sqlite3.connect('my_bot.db') as local_db:
        local_db.execute(
            "INSERT INTO files (name, uid, file_path) VALUES (?, ?, ?)", 
            (full_file_name, user_id, file_path)
        )
        
    return {"status": "success", "message": f"Конспект {full_file_name} успешно сохранен!"}