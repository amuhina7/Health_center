import asyncpg
from datetime import datetime
from config import DB_CONFIG

db_pool = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        **DB_CONFIG,
        min_size=1,
        max_size=10
    )
    print("DATABASE CONNECTED")

async def get_employee_by_code(code: str):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM employees WHERE employee_code = $1 AND is_active = TRUE",
            code
        )

async def get_services():
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM services WHERE is_active = TRUE ORDER BY name"
        )

async def get_doctors_by_service(service_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT d.id, d.full_name, d.specialization
            FROM doctors d
            JOIN doctor_services ds ON ds.doctor_id = d.id
            WHERE ds.service_id = $1 AND d.is_active = TRUE
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
            WHERE doctor_id = $1 AND appointment_date = $2 AND status = 'active'
            """,
            doctor_id, date_obj
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
            WHERE a.vk_user_id = $1 AND a.status = 'active'
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
            WHERE id = $1 AND vk_user_id = $2
            """,
            appointment_id, vk_user_id
        )