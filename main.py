import ssl
import aiohttp
from vkbottle import Bot, AiohttpClient
from config import TOKEN
from database import init_db
from handlers import bl

# Инициализируем бота
bot = Bot(token=TOKEN)

# Интегрируем ветку хэндлеров из файла handlers.py в основного бота
bot.labeler.load(bl)

async def on_startup():
    # 1. Подключаем базу данных
    await init_db()
    
    # 2. Настраиваем SSL-контекст для обхода возможных ошибок сертификации
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 3. Собираем кастомную aiohttp-сессию
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    custom_session = aiohttp.ClientSession(connector=connector)
    
    # 4. Внедряем сессию в http-клиент vkbottle
    bot.api.http_client = AiohttpClient(session=custom_session)
    print("SSL FIX APPLIED SUCCESSFULLY")

if __name__ == "__main__":
    bot.loop_wrapper.add_task(on_startup())
    print("BOT STARTED")
    bot.run_forever()