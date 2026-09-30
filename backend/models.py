from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from .database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)

    # Основная информация о пациенте
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    address = Column(String(255))
    passport_series = Column(String(50))


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    room_number = Column(String(20))


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))

    appointment_time = Column(DateTime)
    status = Column(String(20))

    # Данные очереди
    queue_number = Column(Integer)

    # Жалоба пациента при конкретном обращении
    complaint = Column(String(500))

    # Время консультации
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    # Результат консультации
    visit_type = Column(String(100))
    reason = Column(String(255))