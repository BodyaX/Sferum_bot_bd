import sqlite3
import time
from pathlib import Path
from fastapi import FastAPI, Request
import httpx
import uvicorn

STORAGE_DIR = Path("Files") #задается путь к папке
STORAGE_DIR.mkdir(parents=True, exist_ok=True) #создает папку на диске
DB_NAME = "my_bot.db" #фиксируется имя файла для бд

# Инициализация БД
with sqlite3.connect(DB_NAME) as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    """)

app = FastAPI()

@app.post("/repo") 
async def upload_file(req: Request):
    try: #проверка валидности  JSON
        data = await req.json()
    except Exception:
        return {"status": "error", "detail": "Invalid JSON"}

    sender = data.get("sender", {})  #достаем инфу об отправителе
    user_id = str(sender.get("userId") or sender.get("uid", "unknown")) #скрипт вытаскивает ключ userId если его нет ищет uid
    
    # Берем время из JSON или текущее(если серверного нету у нас)
    try:
        timestamp = int(data.get("timestamp", time.time()))
    except ValueError:
        timestamp = int(time.time())

    attachments = data.get("attachments", []) #скрипт пытается достать вложение из присланного JSON
    if not isinstance(attachments, list): #строгая проверка типа даных, (attacgments именно список)
        return {"status": "error", "detail": "attachments must be a list"}
    # создаем пустой список
    saved_files = []

    # Открываем БД один раз на весь запрос
    with sqlite3.connect(DB_NAME) as db_conn:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for idx, attachment in enumerate(attachments):
                file_url = attachment.get("url")
                raw_filename = attachment.get("filename")

                if not file_url or not raw_filename:
                    continue

                # Формируем безопасное имя для сохранения на диск
                original_filename = Path(raw_filename).name
                safe_disk_filename = f"{timestamp}_{idx}_{original_filename}"
                file_path = STORAGE_DIR / safe_disk_filename

                # Качаем файл
                res = await client.get(file_url)
                if res.status_code != 200:
                    print(f"Не удалось скачать: {original_filename}")
                    continue  # Пропускаем файл и идем к следующему

                # Сохраняем на диск
                with open(file_path, "wb") as f:
                    f.write(res.content)

                # Пишем в базу
                db_conn.execute(
                    "INSERT INTO files (user_id, file_name, file_path, timestamp) VALUES (?, ?, ?, ?)",
                    (user_id, original_filename, str(file_path), timestamp)
                )
                saved_files.append(str(file_path))
        
        db_conn.commit()

    return {"status": "success", "saved": saved_files}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=60001)