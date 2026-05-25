# =========================================
# IMPORTS
# =========================================

import os
import ssl
import aiohttp
import asyncpg

from dotenv import load_dotenv
from datetime import datetime, timedelta

from vkbottle import (
    Bot,
    Keyboard,
    KeyboardButtonColor,
    Text,
    API,
    AiohttpClient,
    CtxStorage
)

from vkbottle.bot import (
    BotLabeler,
    Message
)

# =========================================
# LOAD ENV
# =========================================

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT"))
}

# =========================================
# VK INIT
# =========================================

labeler = BotLabeler()
ctx_storage = CtxStorage()

# Создаем бота со стандартным API. SSL-фикс применим позже, внутри loop.
bot = Bot(
    token=TOKEN,
    labeler=labeler
)

# =========================================
# DATABASE
# =========================================

db_pool = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        **DB_CONFIG,
        min_size=1,
        max_size=10
    )
    print("DATABASE CONNECTED")

# =========================================
# DATABASE FUNCTIONS
# =========================================

async def get_employee_by_code(code: str):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM employees
            WHERE employee_code = $1
            AND is_active = TRUE
            """,
            code
        )

async def get_services():
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM services
            WHERE is_active = TRUE
            ORDER BY name
            """
        )

async def get_doctors_by_service(service_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                d.id,
                d.full_name,
                d.specialization
            FROM doctors d
            JOIN doctor_services ds ON ds.doctor_id = d.id
            WHERE ds.service_id = $1
            AND d.is_active = TRUE
            ORDER BY d.full_name
            """,
            service_id
        )

async def get_appointments_by_datetime(doctor_id, date_iso):
    date_obj = datetime.strptime(date_iso, "%Y-%m-%d").date()
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT appointment_time
            FROM appointments
            WHERE doctor_id = $1
            AND appointment_date = $2
            AND status = 'active'
            """,
            doctor_id,
            date_obj
        )

async def create_appointment(vk_user_id, employee_id, doctor_id, service_id, date_iso, time_str):
    date_obj = datetime.strptime(date_iso, "%Y-%m-%d").date()
    time_obj = datetime.strptime(time_str, "%H:%M").time()
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO appointments (
                vk_user_id, employee_id, doctor_id, service_id, appointment_date, appointment_time
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            vk_user_id, employee_id, doctor_id, service_id, date_obj, time_obj
        )

async def get_user_appointments(vk_user_id):
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                a.id,
                s.name AS service_name,
                d.full_name AS doctor_name,
                a.appointment_date,
                a.appointment_time
            FROM appointments a
            JOIN services s ON s.id = a.service_id
            JOIN doctors d ON d.id = a.doctor_id
            WHERE a.vk_user_id = $1
            AND a.status = 'active'
            ORDER BY a.appointment_date
            """,
            vk_user_id
        )

async def cancel_appointment(appointment_id, vk_user_id):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE appointments
            SET status = 'cancelled'
            WHERE id = $1
            AND vk_user_id = $2
            """,
            appointment_id,
            vk_user_id
        )

# =========================================
# TIME LOGIC
# =========================================

def generate_times():
    times = []
    start = 9
    end = 17
    for hour in range(start, end):
        times.append(f"{hour:02}:00")
        times.append(f"{hour:02}:30")
    return times

async def get_free_times(doctor_id, date_iso):
    all_times = generate_times()
    booked = await get_appointments_by_datetime(doctor_id, date_iso)

    booked_times = {
        row["appointment_time"].strftime("%H:%M") if hasattr(row["appointment_time"], "strftime") else str(row["appointment_time"])[:5]
        for row in booked
    }

    return [t for t in all_times if t not in booked_times]

# =========================================
# KEYBOARDS
# =========================================

async def get_services_keyboard():
    kb = Keyboard(one_time=False)
    services = await get_services()

    for i, service in enumerate(services):
        kb.add(
            Text(
                service["name"],
                {
                    "cmd": "service",
                    "service_id": service["id"],
                    "service_name": service["name"]
                }
            )
        )
        if (i + 1) % 2 == 0:
            kb.row()

    if services and len(services) % 2 != 0:
        kb.row()

    kb.add(
        Text("📋 Мои записи", {"cmd": "my_appointments"}),
        color=KeyboardButtonColor.SECONDARY
    )
    return kb.get_json()

async def get_doctors_keyboard(service_id):
    doctors = await get_doctors_by_service(service_id)
    if not doctors:
        return None

    kb = Keyboard(one_time=False)
    for i, doctor in enumerate(doctors):
        kb.add(
            Text(
                doctor["full_name"],
                {
                    "cmd": "doctor",
                    "doctor_id": doctor["id"],
                    "doctor_name": doctor["full_name"]
                }
            )
        )
        if (i + 1) % 2 == 0:
            kb.row()

    return kb.get_json()

def get_calendar_keyboard():
    kb = Keyboard(one_time=False)
    today = datetime.now().date()
    count = 0

    for i in range(14):
        current = today + timedelta(days=i)
        if current.weekday() >= 5:
            continue

        date_iso = current.strftime("%Y-%m-%d")
        display = current.strftime("%d.%m")

        kb.add(Text(display, {"cmd": "date", "date": date_iso}))
        count += 1
        if count % 3 == 0:
            kb.row()

    return kb.get_json()

def get_time_keyboard(times):
    kb = Keyboard(one_time=False)
    for i, t in enumerate(times):
        kb.add(Text(t, {"cmd": "time", "time": t}))
        if (i + 1) % 3 == 0:
            kb.row()
    return kb.get_json()

# =========================================
# HANDLERS
# =========================================

@bot.on.message(text=["start", "/start", "начать", "привет"])
async def start(message: Message):
    print("MESSAGE START:", message.text)
    keys_to_clear = [
        "step", "employee_id", "employee_name", 
        "service_id", "service_name", "doctor_id", 
        "doctor_name", "date"
    ]

    for key in keys_to_clear:
        ctx_storage.set(f"{message.peer_id}_{key}", None)

    ctx_storage.set(f"{message.peer_id}_step", "WAIT_EMPLOYEE_CODE")

    await message.answer(
        "🏥 Здравпункт завода им. Петровского\n\n"
        "Введите ваш табельный номер:"
    )

# =========================================
# SERVICE BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "service"})
async def choose_service(message: Message):
    payload = message.get_payload_json()
    ctx_storage.set(f"{message.peer_id}_service_id", payload["service_id"])
    ctx_storage.set(f"{message.peer_id}_service_name", payload["service_name"])
    ctx_storage.set(f"{message.peer_id}_step", "WAIT_DOCTOR")

    keyboard = await get_doctors_keyboard(payload["service_id"])
    if not keyboard:
        await message.answer("❌ Для данной услуги врачи не найдены.")   
        return

    await message.answer("👨‍⚕️ Выберите врача:", keyboard=keyboard)

# =========================================
# DOCTOR BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "doctor"})
async def choose_doctor(message: Message):
    payload = message.get_payload_json()
    ctx_storage.set(f"{message.peer_id}_doctor_id", payload["doctor_id"])
    ctx_storage.set(f"{message.peer_id}_doctor_name", payload["doctor_name"])
    ctx_storage.set(f"{message.peer_id}_step", "WAIT_DATE")

    await message.answer("📅 Выберите дату:", keyboard=get_calendar_keyboard())

# =========================================
# DATE BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "date"})
async def choose_date(message: Message):
    payload = message.get_payload_json()
    date_iso = payload["date"]
    doctor_id = ctx_storage.get(f"{message.peer_id}_doctor_id")

    free_times = await get_free_times(doctor_id, date_iso)
    if not free_times:
        await message.answer("❌ Нет свободного времени на эту дату.")
        return

    ctx_storage.set(f"{message.peer_id}_date", date_iso)
    ctx_storage.set(f"{message.peer_id}_step", "WAIT_TIME")

    await message.answer("⏰ Выберите время:", keyboard=get_time_keyboard(free_times))

# =========================================
# TIME BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "time"})
async def choose_time(message: Message):
    payload = message.get_payload_json()
    time_str = payload["time"]

    employee_id = ctx_storage.get(f"{message.peer_id}_employee_id")
    employee_name = ctx_storage.get(f"{message.peer_id}_employee_name")
    doctor_id = ctx_storage.get(f"{message.peer_id}_doctor_id")
    doctor_name = ctx_storage.get(f"{message.peer_id}_doctor_name")
    service_id = ctx_storage.get(f"{message.peer_id}_service_id")
    service_name = ctx_storage.get(f"{message.peer_id}_service_name")
    date_iso = ctx_storage.get(f"{message.peer_id}_date")

    await create_appointment(
        message.from_id, employee_id, doctor_id, 
        service_id, date_iso, time_str
    )

    formatted_date = datetime.strptime(date_iso, '%Y-%m-%d').strftime('%d.%m.%Y')

    await message.answer(
        f"✅ Запись подтверждена\n\n"
        f"👤 Сотрудник:\n{employee_name}\n\n"
        f"🩺 Услуга:\n{service_name}\n\n"
        f"👨‍⚕️ Врач:\n{doctor_name}\n\n"
        f"📅 Дата:\n{formatted_date}\n\n"
        f"⏰ Время:\n{time_str}",
        keyboard=await get_services_keyboard()
    )

# =========================================
# MY APPOINTMENTS BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "my_appointments"})
async def my_appointments(message: Message):
    appointments = await get_user_appointments(message.from_id)
    if not appointments:
        await message.answer("У вас нет активных записей.")
        return

    text = "📋 Ваши записи:\n\n"
    kb = Keyboard(one_time=False)

    for a in appointments:
        date_str = a['appointment_date'].strftime('%d.%m.%Y') if hasattr(a['appointment_date'], 'strftime') else str(a['appointment_date'])
        time_str = a['appointment_time'].strftime('%H:%M') if hasattr(a['appointment_time'], 'strftime') else str(a['appointment_time'])[:5]

        text += (
            f"🩺 {a['service_name']}\n"
            f"👨‍⚕️ {a['doctor_name']}\n"
            f"📅 {date_str}\n"
            f"⏰ {time_str}\n\n"
        )
        kb.add(
            Text(
                f"❌ Отменить #{a['id']}",
                {"cmd": "cancel_appointment", "appointment_id": a["id"]}
            )
        )
        kb.row()

    await message.answer(text, keyboard=kb.get_json())

# =========================================
# CANCEL BUTTON
# =========================================
@bot.on.message(payload_map={"cmd": "cancel_appointment"})
async def cancel(message: Message):
    payload = message.get_payload_json()
    await cancel_appointment(payload["appointment_id"], message.from_id)

    await message.answer(
        "❌ Запись отменена.",
        keyboard=await get_services_keyboard()
    )

# =========================================
# MAIN HANDLER (CATCH-ALL TEXT INPUT)
# =========================================
@bot.on.message()
async def main_handler(message: Message):
    if message.payload:
        return

    print("MAIN HANDLER MSG:", message.text)
    step = ctx_storage.get(f"{message.peer_id}_step")

    if step == "WAIT_EMPLOYEE_CODE":
        code = message.text.strip()
        employee = await get_employee_by_code(code)

        if not employee:
            await message.answer(
                "❌ Сотрудник не найден.\n"
                "Проверьте табельный номер."
            )
            return

        ctx_storage.set(f"{message.peer_id}_employee_id", employee["id"])
        ctx_storage.set(f"{message.peer_id}_employee_name", employee["full_name"])
        ctx_storage.set(f"{message.peer_id}_step", "WAIT_SERVICE")

        await message.answer(
            f"✅ Сотрудник найден:\n{employee['full_name']}\n\nВыберите услугу:",
            keyboard=await get_services_keyboard()
        )
        return

# =========================================
# STARTUP & RUN
# =========================================

async def on_startup():
    # 1. Сначала поднимаем базу данных
    await init_db()
    
    # 2. Настраиваем SSL-контекст (теперь безопасно внутри запущенного loop)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 3. Собираем сессию со свободными правилами для SSL
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    custom_session = aiohttp.ClientSession(connector=connector)
    
    # 4. Передаем готовую сессию в http_client нашего бота
    bot.api.http_client = AiohttpClient(session=custom_session)
    print("SSL FIX APPLIED SUCCESSFULY")

if __name__ == "__main__":
    bot.loop_wrapper.add_task(on_startup())
    print("BOT STARTED")
    bot.run_forever()