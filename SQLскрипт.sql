


-- =========================================
-- СОТРУДНИКИ ЗАВОДА
-- =========================================

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,

    employee_code VARCHAR(20) UNIQUE NOT NULL,

    full_name TEXT NOT NULL,

    department TEXT,
    workshop TEXT,
    position_name TEXT,

    phone VARCHAR(30),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);


-- =========================================
-- ВРАЧИ
-- =========================================

CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,

    full_name TEXT NOT NULL,

    specialization TEXT NOT NULL,

    cabinet VARCHAR(20),

    phone VARCHAR(30),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);


-- =========================================
-- УСЛУГИ
-- =========================================

CREATE TABLE services (
    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE NOT NULL,

    duration_minutes INTEGER DEFAULT 30,

    description TEXT,

    is_active BOOLEAN DEFAULT TRUE
);


-- =========================================
-- СВЯЗЬ ВРАЧЕЙ И УСЛУГ
-- =========================================

CREATE TABLE doctor_services (
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,

    PRIMARY KEY (doctor_id, service_id)
);


-- =========================================
-- РАСПИСАНИЕ ВРАЧЕЙ
-- weekday:
-- 1 = ПН
-- 2 = ВТ
-- 3 = СР
-- 4 = ЧТ
-- 5 = ПТ
-- 6 = СБ
-- 7 = ВС
-- =========================================

CREATE TABLE doctor_schedule (
    id SERIAL PRIMARY KEY,

    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,

    weekday INTEGER NOT NULL CHECK (weekday BETWEEN 1 AND 7),

    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    break_start TIME,
    break_end TIME
);


-- =========================================
-- ЗАПИСИ НА ПРИЕМ
-- =========================================

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,

    vk_user_id BIGINT NOT NULL,

    employee_id INTEGER NOT NULL REFERENCES employees(id),

    doctor_id INTEGER NOT NULL REFERENCES doctors(id),

    service_id INTEGER NOT NULL REFERENCES services(id),

    appointment_date DATE NOT NULL,

    appointment_time TIME NOT NULL,

    status VARCHAR(20) DEFAULT 'active',

    comment TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (
        status IN (
            'active',
            'cancelled',
            'completed',
            'missed'
        )
    )
);


-- =========================================
-- УНИКАЛЬНОСТЬ ВРЕМЕНИ У ВРАЧА
-- =========================================

CREATE UNIQUE INDEX unique_doctor_datetime
ON appointments(
    doctor_id,
    appointment_date,
    appointment_time
);


-- =========================================
-- ИНДЕКСЫ
-- =========================================

CREATE INDEX idx_employee_code
ON employees(employee_code);

CREATE INDEX idx_appointments_date
ON appointments(appointment_date);

CREATE INDEX idx_appointments_vk_user
ON appointments(vk_user_id);

CREATE INDEX idx_appointments_status
ON appointments(status);


-- =========================================
-- ТЕСТОВЫЕ СОТРУДНИКИ
-- =========================================

INSERT INTO employees (
    employee_code,
    full_name,
    department,
    workshop,
    position_name,
    phone
)
VALUES
('1001', 'Иванов Сергей Петрович', 'Производство', 'Цех №1', 'Токарь', '+79990000001'),
('1002', 'Петров Алексей Викторович', 'Металлургия', 'Цех №2', 'Сварщик', '+79990000002'),
('1003', 'Сидоров Николай Иванович', 'Сборка', 'Цех №3', 'Слесарь', '+79990000003'),
('1004', 'Кузнецов Андрей Павлович', 'Энергетика', 'Цех №4', 'Электрик', '+79990000004'),
('1005', 'Смирнов Дмитрий Олегович', 'Логистика', 'Склад', 'Кладовщик', '+79990000005'),
('1006', 'Васильев Игорь Сергеевич', 'ОТК', 'Контроль', 'Инженер ОТК', '+79990000006'),
('1007', 'Морозова Елена Викторовна', 'Бухгалтерия', 'Администрация', 'Бухгалтер', '+79990000007'),
('1008', 'Попов Максим Андреевич', 'Производство', 'Цех №5', 'Оператор станка', '+79990000008');


-- =========================================
-- ВРАЧИ
-- =========================================

INSERT INTO doctors (
    full_name,
    specialization,
    cabinet,
    phone
)
VALUES
('Петрова Анна Сергеевна', 'Терапевт', '101', '+79991111111'),
('Смирнова Ольга Викторовна', 'Кардиолог', '102', '+79992222222'),
('Кузнецов Михаил Андреевич', 'Хирург', '103', '+79993333333'),
('Волкова Ирина Павловна', 'Фельдшер', '104', '+79994444444'),
('Орлов Дмитрий Николаевич', 'Невролог', '105', '+79995555555');


-- =========================================
-- УСЛУГИ
-- =========================================

INSERT INTO services (
    name,
    duration_minutes,
    description
)
VALUES
('Терапевт', 30, 'Консультация терапевта'),
('ЭКГ', 20, 'Электрокардиограмма'),
('Измерение давления', 10, 'Контроль артериального давления'),
('Медосмотр', 40, 'Плановый медицинский осмотр'),
('Перевязка', 20, 'Обработка и перевязка'),
('Инъекция', 15, 'Внутримышечная инъекция'),
('Выдача справки', 15, 'Оформление медицинской справки'),
('Предсменный осмотр', 10, 'Осмотр перед сменой'),
('Послесменный осмотр', 10, 'Осмотр после смены'),
('Вакцинация', 20, 'Профилактическая вакцинация');


-- =========================================
-- СВЯЗЬ ВРАЧЕЙ И УСЛУГ
-- =========================================

INSERT INTO doctor_services (doctor_id, service_id)
VALUES

-- Терапевт
(1, 1),
(1, 3),
(1, 4),
(1, 7),
(1, 8),
(1, 9),

-- Кардиолог
(2, 2),
(2, 3),
(2, 4),

-- Хирург
(3, 5),
(3, 6),

-- Фельдшер
(4, 3),
(4, 6),
(4, 8),
(4, 9),
(4, 10),

-- Невролог
(5, 1),
(5, 4);


-- =========================================
-- РАСПИСАНИЕ ВРАЧЕЙ
-- =========================================

INSERT INTO doctor_schedule (
    doctor_id,
    weekday,
    start_time,
    end_time,
    break_start,
    break_end
)
VALUES

-- Терапевт
(1, 1, '09:00', '17:00', '13:00', '14:00'),
(1, 2, '09:00', '17:00', '13:00', '14:00'),
(1, 3, '09:00', '17:00', '13:00', '14:00'),
(1, 4, '09:00', '17:00', '13:00', '14:00'),
(1, 5, '09:00', '17:00', '13:00', '14:00'),

-- Кардиолог
(2, 1, '10:00', '16:00', '13:00', '13:30'),
(2, 3, '10:00', '16:00', '13:00', '13:30'),
(2, 5, '10:00', '16:00', '13:00', '13:30'),

-- Хирург
(3, 2, '09:00', '15:00', '12:00', '12:30'),
(3, 4, '09:00', '15:00', '12:00', '12:30'),

-- Фельдшер
(4, 1, '08:00', '18:00', '12:00', '13:00'),
(4, 2, '08:00', '18:00', '12:00', '13:00'),
(4, 3, '08:00', '18:00', '12:00', '13:00'),
(4, 4, '08:00', '18:00', '12:00', '13:00'),
(4, 5, '08:00', '18:00', '12:00', '13:00'),

-- Невролог
(5, 2, '11:00', '17:00', '14:00', '14:30'),
(5, 4, '11:00', '17:00', '14:00', '14:30');


-- =========================================
-- ТЕСТОВЫЕ ЗАПИСИ
-- =========================================

INSERT INTO appointments (
    vk_user_id,
    employee_id,
    doctor_id,
    service_id,
    appointment_date,
    appointment_time,
    status
)
VALUES
(111111111, 1, 1, 1, CURRENT_DATE + INTERVAL '1 day', '10:00', 'active'),
(222222222, 2, 2, 2, CURRENT_DATE + INTERVAL '2 day', '11:00', 'active'),
(333333333, 3, 4, 10, CURRENT_DATE + INTERVAL '3 day', '09:00', 'active');

CREATE USER health_user
WITH
PASSWORD '123';

ALTER ROLE health_user SET client_encoding TO 'utf8';

ALTER ROLE health_user SET default_transaction_isolation TO 'read committed';

ALTER ROLE health_user SET timezone TO 'Europe/Moscow';

GRANT ALL PRIVILEGES
ON ALL TABLES IN SCHEMA public
TO health_user;

GRANT ALL PRIVILEGES
ON ALL SEQUENCES IN SCHEMA public
TO health_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO health_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO health_user;