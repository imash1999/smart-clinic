from fastapi import Depends, FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from .kafka_producer import publish_event

from backend.utils.priority import calculate_priority
from .routing import determine_specialty
from .database import Base, engine, get_db
from .models import Patient,Doctor,Department,Appointment
from .schemas import (
    PatientCreate,
    PatientResponse,
    DoctorCreate,
    DoctorResponse,
    DepartmentCreate,
    DepartmentResponse,
    AppointmentCreate,
    AppointmentResponse,
    AppointmentDetailResponse,
    AppointmentFinish,
    AppointmentFinishResponse,
    RegistrationCreate,
    RegistrationResponse,
    QueueStatusResponse
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Clinic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Smart Clinic API is running"}


@app.post("/patients", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    new_patient = Patient(
        name=patient.name,
        phone=patient.phone,
        address=patient.address,
        passport_series=patient.passport_series
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return new_patient

@app.get("/patients",response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

@app.post("/registration", response_model=RegistrationResponse)
def registration(
    registration: RegistrationCreate,
    db: Session = Depends(get_db)
):
    # 1. Определяем специальность по жалобе пациента
    specialty = determine_specialty(registration.complaint)

    # 2. Ищем врача этой специальности
    doctor = (
        db.query(Doctor)
        .filter(Doctor.specialty == specialty)
        .first()
    )

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail=f"No doctor found for specialty: {specialty}"
        )

    # 3. Ищем отделение с соответствующим названием
    department_names = {
        "Therapist": "Therapy",
        "Cardiologist": "Cardiology",
        "Neurologist": "Neurology"
    }

    department_name = department_names.get(specialty)

    if department_name is None:
        raise HTTPException(
            status_code=404,
            detail=f"No department configured for specialty: {specialty}"
        )

    department = (
        db.query(Department)
        .filter(Department.name == department_name)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail=f"Department not found: {department_name}"
        )

    # 4. Создаём пациента
    new_patient = Patient(
        name=registration.name,
        phone=registration.phone,
        address=registration.address,
        passport_series=registration.passport_series
    )

    db.add(new_patient)
    db.flush()

    # 5. Получаем следующий номер очереди этого врача
    last_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.queue_number.isnot(None)
        )
        .order_by(Appointment.queue_number.desc())
        .first()
    )

    if last_appointment and last_appointment.queue_number:
        queue_number = last_appointment.queue_number + 1
    else:
        queue_number = 1

    # 6. Создаём запись на приём
    new_appointment = Appointment(
        patient_id=new_patient.id,
        doctor_id=doctor.id,
        department_id=department.id,
        appointment_time=datetime.now(),
        status="BOOKED",
        queue_number=queue_number,
        priority=calculate_priority(registration.complaint),
        complaint=registration.complaint
    )

    db.add(new_appointment)

    # 7. Сохраняем пациента и запись
    db.commit()

    db.refresh(new_patient)
    db.refresh(new_appointment)

    return {
        "patient": new_patient,
        "appointment": new_appointment,
        "specialty": specialty
    }

@app.post("/doctors", response_model=DoctorResponse)
def create_doctor(
    doctor: DoctorCreate,
    db: Session = Depends(get_db)
):
    new_doctor = Doctor(
        name=doctor.name,
        specialty=doctor.specialty
    )

    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)

    return new_doctor

@app.get("/doctors",response_model=list[DoctorResponse])
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return doctors 

@app.post("/appointments", response_model=AppointmentResponse)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db)
):
    new_appointment = Appointment(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        department_id=appointment.department_id,
        appointment_time=appointment.appointment_time,
        status=appointment.status
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment


@app.get("/appointments", response_model=list[AppointmentResponse])
def get_appointments(db: Session = Depends(get_db)):
    appointments = db.query(Appointment).all()
    return appointments

@app.post("/departments", response_model=DepartmentResponse)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db)
):
    new_department = Department(
        name=department.name
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    return new_department


@app.get("/departments", response_model=list[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return departments

@app.post("/appointments/{appointment_id}/start", response_model=AppointmentResponse)
def start_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "WAITING":
        raise HTTPException(
            status_code=400,
            detail="Appointment must be WAITING before starting"
        )

    appointment.status = "IN_PROGRESS"
    appointment.started_at = datetime.now()

    publish_event(
        topic="consultation-events",
        event={
            "event_type": "appointment_started",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "started_at": appointment.started_at,
        }
    )

    db.commit()
    db.refresh(appointment)

    return appointment

@app.post("/appointments/{appointment_id}/arrive", response_model=AppointmentResponse)
def arrive_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "BOOKED":
        raise HTTPException(
            status_code=400,
            detail="Only BOOKED appointments can be marked as ARRIVED"
        )

    appointment.status = "ARRIVED"

    db.commit()
    db.refresh(appointment)
    
    publish_event(
        topic="patient-events",
        event={
            "event_type": "patient_arrived",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
        }
    )

    return appointment

@app.post("/appointments/{appointment_id}/finish", response_model=AppointmentFinishResponse)
def finish_appointment(
    appointment_id: int,
    finish_data: AppointmentFinish,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS appointments can be finished"
        )

    appointment.status = "COMPLETED"
    appointment.finished_at = datetime.now()
    appointment.visit_type = finish_data.visit_type
    appointment.reason = finish_data.reason
    appointment.diagnosis = finish_data.diagnosis

    db.commit()
    db.refresh(appointment)
        # Публикуем событие в Kafka
    publish_event(
        topic="consultation-events",
        event={
            "event_type": "appointment_finished",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "started_at": appointment.started_at,
            "finished_at": appointment.finished_at,
            "visit_type": appointment.visit_type,
            "reason": appointment.reason,
        }
    )

    # Ищем следующего WAITING-пациента этого врача
    next_patient = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.status == "WAITING"
        )
        .order_by(Appointment.queue_number)
        .first()
    )

    return {
        "finished": appointment,
        "next_patient": next_patient
    }

@app.get("/appointments/{appointment_id}", response_model=AppointmentDetailResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    duration_seconds = None

    if appointment.started_at and appointment.finished_at:
        duration_seconds = int(
            (appointment.finished_at - appointment.started_at).total_seconds()
        )
    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id
    ).first()

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    department = db.query(Department).filter(
        Department.id == appointment.department_id
    ).first()

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return {
    "id": appointment.id,
    "patient_id": appointment.patient_id,
    "doctor_id": appointment.doctor_id,
    "doctor_name": doctor.name,
    "room_number": doctor.room_number,
    "department_id": appointment.department_id,
    "department_name": department.name,
    "appointment_time": appointment.appointment_time,
    "status": appointment.status,
    "queue_number": appointment.queue_number,
    "priority": appointment.priority,
    "complaint": appointment.complaint,
    "started_at": appointment.started_at,
    "finished_at": appointment.finished_at,
    "duration_seconds": duration_seconds,
    "visit_type": appointment.visit_type,
    "reason": appointment.reason,
    "diagnosis": appointment.diagnosis
    }

@app.post("/appointments/{appointment_id}/waiting", response_model=AppointmentResponse)
def waiting_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "ARRIVED":
        raise HTTPException(
            status_code=400,
            detail="Only ARRIVED appointments can enter the waiting queue"
        )

    appointment.status = "WAITING"

    publish_event(
        topic="queue-events",
        event={
            "event_type": "appointment_waiting",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "appointment_time": appointment.appointment_time,
        }
    )


    db.commit()
    db.refresh(appointment)

    return appointment

@app.get("/doctors/{doctor_id}/queue")
def get_doctor_queue(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "WAITING"
        )
        .order_by(
            Appointment.priority.desc(),
            Appointment.queue_number.asc()
        )
        .all()
    )

    return appointments

@app.get("/doctors/{doctor_id}/next-patient")
def get_next_patient(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "WAITING"
        )
        .order_by(Appointment.queue_number)
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="No patients waiting"
        )

    return appointment

@app.get("/doctors/{doctor_id}/current-patient")
def get_current_patient(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "IN_PROGRESS"
        )
        .order_by(Appointment.queue_number)
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="No patient is currently being examined"
        )

    patient = db.query(Patient).filter(
        Patient.id == appointment.patient_id
    ).first()

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return {
        "id": appointment.id,
        "patient_id": patient.id,
        "patient_name": patient.name,
        "phone": patient.phone,
        "address": patient.address,
        "passport_series": patient.passport_series,
        "doctor_id": appointment.doctor_id,
        "department_id": appointment.department_id,
        "queue_number": appointment.queue_number,
        "status": appointment.status,
        "complaint": appointment.complaint,
        "started_at": appointment.started_at,
        "finished_at": appointment.finished_at,
        "visit_type": appointment.visit_type,
        "reason": appointment.reason
    }

@app.post("/doctors/{doctor_id}/start-next")
def start_next_patient(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "WAITING"
        )
        .order_by(
            Appointment.priority.desc(),
            Appointment.queue_number.asc()
        )
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="No waiting patients"
        )

    appointment.status = "IN_PROGRESS"
    appointment.started_at = datetime.now()

    db.commit()
    db.refresh(appointment)

    publish_event(
        topic="consultation-events",
        event={
            "event_type": "appointment_started",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "started_at": appointment.started_at,
        }
    )

    return appointment

@app.post("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "BOOKED":
        raise HTTPException(
            status_code=400,
            detail="Only BOOKED appointments can be cancelled"
        )

    appointment.status = "CANCELLED"

    publish_event(
        topic="appointment-events",
        event={
            "event_type": "appointment_cancelled",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "appointment_time": appointment.appointment_time,
        }
    )

    db.commit()
    db.refresh(appointment)

    return appointment


@app.post("/appointments/{appointment_id}/no-show", response_model=AppointmentResponse)
def no_show_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "BOOKED":
        raise HTTPException(
            status_code=400,
            detail="Only BOOKED appointments can be marked as NO_SHOW"
        )

    appointment.status = "NO_SHOW"

    publish_event(
        topic="appointment-events",
        event={
            "event_type": "appointment_no_show",
            "appointment_id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "department_id": appointment.department_id,
            "appointment_time": appointment.appointment_time,
        }
    )

    db.commit()
    db.refresh(appointment)

    return appointment

@app.get(
    "/appointments/{appointment_id}/queue-status",
    response_model=QueueStatusResponse
)
def get_queue_status(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.queue_number is None:
        raise HTTPException(
            status_code=400,
            detail="Appointment has no queue number"
        )

    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id
    ).first()

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    # Пациенты этого же врача, которые находятся
    # перед текущим пациентом и реально ждут
    people_ahead = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.queue_number < appointment.queue_number,
        Appointment.status.in_(["ARRIVED", "WAITING"])
    ).count()

    # Пациент, которого врач сейчас принимает
    current_patient = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.status == "IN_PROGRESS"
    ).order_by(
        Appointment.queue_number
    ).first()

    # Если сейчас никто не принимается,
    # показываем первого ожидающего
    if current_patient:
        current_queue_number = current_patient.queue_number
    else:
        current_queue_number = None

    next_patient = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.status.in_(["ARRIVED", "WAITING"])
    ).order_by(
        Appointment.queue_number
    ).first()

    next_queue_number = (
        next_patient.queue_number
        if next_patient
        else None
    )

    return {
        "appointment_id": appointment.id,
        "queue_number": appointment.queue_number,
        "status": appointment.status,
        "people_ahead": people_ahead,
        "current_queue_number": current_queue_number,
        "doctor_name": doctor.name,
        "room_number": doctor.room_number,
        "next_queue_number": next_queue_number
    }

@app.get("/patients/{patient_id}/history")
def get_patient_history(
    patient_id: int,
    db: Session = Depends(get_db)
):

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "COMPLETED"
        )
        .order_by(Appointment.finished_at.desc())
        .all()
    )


    result = []

    for appointment in appointments:

        doctor = (
            db.query(Doctor)
            .filter(
                Doctor.id == appointment.doctor_id
            )
            .first()
        )

        department = (
            db.query(Department)
            .filter(
                Department.id == appointment.department_id
            )
            .first()
        )


        result.append({

            "id": appointment.id,

            "finished_at": appointment.finished_at,

            "complaint": appointment.complaint,

            "visit_type": appointment.visit_type,

            "reason": appointment.reason,

            "diagnosis": appointment.diagnosis,

            "doctor_name":
                doctor.name if doctor else "-",

            "department_name":
                department.name if department else "-"

        })


    return result

@app.get("/patients/search")
def search_patient(
    phone: str,
    db: Session = Depends(get_db)
):

    patient = (
        db.query(Patient)
        .filter(
            Patient.phone == phone
        )
        .first()
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient

@app.get("/analytics/summary")
def get_summary(
    db: Session = Depends(get_db)
):

    total_patients = (
        db.query(Patient)
        .count()
    )


    total_appointments = (
        db.query(Appointment)
        .count()
    )


    completed = (
        db.query(Appointment)
        .filter(
            Appointment.status == "COMPLETED"
        )
        .count()
    )


    waiting = (
        db.query(Appointment)
        .filter(
            Appointment.status == "WAITING"
        )
        .count()
    )


    return {
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "completed": completed,
        "waiting": waiting
    }

@app.get("/analytics/doctors")
def get_doctor_analytics(
    db: Session = Depends(get_db)
):

    doctors = db.query(Doctor).all()

    result = []

    for doctor in doctors:

        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status == "COMPLETED"
            )
            .all()
        )

        total = len(appointments)

        durations = [
            a.duration_seconds
            for a in appointments
            if a.duration_seconds
        ]

        avg_duration = None

        if durations:
            avg_duration = sum(durations) / len(durations)


        result.append({

            "doctor_name": doctor.name,

            "completed_visits": total,

            "average_duration_seconds":
                round(avg_duration, 2)
                if avg_duration else 0

        })


    return result

@app.get("/analytics/departments")
def get_department_analytics(
    db: Session = Depends(get_db)
):

    departments = db.query(Department).all()

    result = []

    for department in departments:

        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.department_id == department.id
            )
            .all()
        )

        completed = [
            a for a in appointments
            if a.status == "COMPLETED"
        ]

        durations = [
            a.duration_seconds
            for a in completed
            if a.duration_seconds
        ]

        avg_duration = 0

        if durations:
            avg_duration = sum(durations) / len(durations)


        result.append({
            "department_name": department.name,
            "total_visits": len(appointments),
            "completed_visits": len(completed),
            "average_duration_seconds": round(avg_duration, 2)
        })


    return result