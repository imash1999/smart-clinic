from fastapi import Depends, FastAPI,HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

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
    AppointmentDetailResponse
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Clinic API")


@app.get("/")
def home():
    return {"message": "Smart Clinic API is running"}


@app.post("/patients", response_model=PatientResponse)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    new_patient = Patient(
        name=patient.name,
        phone=patient.phone
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return new_patient

@app.get("/patients",response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

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

    return appointment

@app.post("/appointments/{appointment_id}/finish", response_model=AppointmentResponse)
def finish_appointment(
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

    if appointment.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS appointments can be finished"
        )

    appointment.status = "COMPLETED"
    appointment.finished_at = datetime.now()

    db.commit()
    db.refresh(appointment)

    return appointment

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

    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "department_id": appointment.department_id,
        "appointment_time": appointment.appointment_time,
        "status": appointment.status,
        "started_at": appointment.started_at,
        "finished_at": appointment.finished_at,
        "duration_seconds": duration_seconds
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
        .order_by(Appointment.appointment_time)
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
        .order_by(Appointment.appointment_time)
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="No patients waiting"
        )

    return appointment
