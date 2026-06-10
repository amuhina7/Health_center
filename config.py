import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else 5432
}

# --- НАШ ДЕБАГ-БЛОК ---
print("\n" + "="*40)
print(f"[CONFIG DEBUG] Проверка переменных окружения:")
print(f" -> DB_HOST: {DB_CONFIG['host']} (Тип: {type(DB_CONFIG['host']).__name__})")
print(f" -> DB_NAME: {DB_CONFIG['database']}")
print(f" -> DB_USER: {DB_CONFIG['user']}")
print(f" -> VK_TOKEN существует?: {'Да' if TOKEN else 'Нет'}")
print("="*40 + "\n")