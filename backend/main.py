from fastapi import Depends, FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from .kafka_producer import publish_event

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
    RegistrationResponse
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

    return {
    "id": appointment.id,
    "patient_id": appointment.patient_id,
    "doctor_id": appointment.doctor_id,
    "doctor_name": doctor.name,
    "room_number": doctor.room_number,
    "department_id": appointment.department_id,
    "appointment_time": appointment.appointment_time,
    "status": appointment.status,
    "queue_number": appointment.queue_number,
    "complaint": appointment.complaint,
    "started_at": appointment.started_at,
    "finished_at": appointment.finished_at,
    "duration_seconds": duration_seconds,
    "visit_type": appointment.visit_type,
    "reason": appointment.reason
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
        .order_by(Appointment.queue_number)
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
        .order_by(Appointment.queue_number)
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