from datetime import datetime
from vkbottle.bot import BotLabeler, Message
from vkbottle import CtxStorage, Keyboard, Text

from database import (
    get_employee_by_code,
    create_appointment,
    get_user_appointments,
    cancel_appointment
)
from utils import get_free_times
from keyboards import (
    get_services_keyboard,
    get_doctors_keyboard,
    get_calendar_keyboard,
    get_time_keyboard
)

# Создаем изолированный лейблер для хэндлеров
bl = BotLabeler()
ctx_storage = CtxStorage()

@bl.message(text=["start", "/start", "начать", "привет"])
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

@bl.message(payload_map={"cmd": "service"})
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

@bl.message(payload_map={"cmd": "doctor"})
async def choose_doctor(message: Message):
    payload = message.get_payload_json()
    ctx_storage.set(f"{message.peer_id}_doctor_id", payload["doctor_id"])
    ctx_storage.set(f"{message.peer_id}_doctor_name", payload["doctor_name"])
    ctx_storage.set(f"{message.peer_id}_step", "WAIT_DATE")

    await message.answer("📅 Выберите дату:", keyboard=get_calendar_keyboard())

@bl.message(payload_map={"cmd": "date"})
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

@bl.message(payload_map={"cmd": "time"})
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

@bl.message(payload_map={"cmd": "my_appointments"})
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

@bl.message(payload_map={"cmd": "cancel_appointment"})
async def cancel(message: Message):
    payload = message.get_payload_json()
    await cancel_appointment(payload["appointment_id"], message.from_id)

    await message.answer(
        "❌ Запись отменена.",
        keyboard=await get_services_keyboard()
    )

@bl.message()
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