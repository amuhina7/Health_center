import ssl
import aiohttp
import traceback
from vkbottle import Bot, AiohttpClient
from config import TOKEN
from database import init_db
from handlers import bl

# Инициализируем бота
bot = Bot(token=TOKEN)

# Интегрируем ветку хэндлеров
bot.labeler.load(bl)

# Асинхронная функция инициализации
async def on_startup():
    try:
        print("--- [START] НАЧАЛО ВЫПОЛНЕНИЯ ON_STARTUP ---")
        print("Подключение к базе данных...")
        await init_db()
        print("База данных успешно подключена!")
        
        # Настраиваем SSL-контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Собираем кастомную сессию
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        custom_session = aiohttp.ClientSession(connector=connector)
        
        bot.api.http_client = AiohttpClient(session=custom_session)
        print("SSL FIX APPLIED SUCCESSFULLY")
        print("--- [SUCCESS] ON_STARTUP ПОЛНОСТЬЮ ВЫПОЛНЕН ---")
    except Exception as e:
        print("\n" + "="*50)
        print("!!! НАЙДЕНА ОШИБКА ВНУТРИ ON_STARTUP !!!")
        print(f"Тип исключения: {type(e).__name__}")
        print(f"Текст ошибки: {e}")
        print("="*50)
        traceback.print_exc()
        print("="*50 + "\n")

if __name__ == "__main__":
    print("BOT STARTED")
    
    # ВЫЗЫВАЕМ функцию скобками (), чтобы передать корутину, как требует vkbottle
    bot.on_startup.append(on_startup())
    
    # Запуск бота
    bot.run()