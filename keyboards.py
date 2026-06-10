from datetime import datetime, timedelta
from vkbottle import Keyboard, KeyboardButtonColor, Text
from database import get_services, get_doctors_by_service

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