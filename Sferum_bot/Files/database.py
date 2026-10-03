import sqlite3
import os
import requests
from fastapi import FastAPI

storage = 'Files'
os.makedirs(storage, exist_ok=True) # Создаем папку, если ее нет

# Подключаемся к бд и создаем таблицу для метаданных.
db = sqlite3.connect('my_bot.db')
sql = db.cursor()
sql.execute("""
create table if not exists files ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    # Лезем внутрь словаря  по ключам и забираем то что нужно
    user_id = str(request_data["sender"]["userId"])
    url = request_data["attachments"]["payload"]["url"]
    token = request_data["attachments"]["payload"]["token"]

    file_name = f"{token}.txt" #берет токен и прибавляет .txt
    file_path = f"{storage}/{file_name}" #имя папки + имя файла

    # Отправляем GET-заропс в хранилище по адресу, в перемнную идет ответ от сервиса с содержимым файла
    res = requests.get(f"{url}/{token}")
    
    # Пишем текст на диск
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(res.text)

    # открыли соединение с БД
    with sqlite3.connect('my_bot.db') as local_db:
        local_db.execute( #выпонили SQL-запрос
            "INSERT INTO files (name, file_path, uid) VALUES (?, ?, ?)",
            (file_name, file_path, user_id)
        )

    return {"status": "success", "file": file_path} #вернули ответ в формате JSON о том что все записалосью