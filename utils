from database import get_appointments_by_datetime

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