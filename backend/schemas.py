from pydantic import BaseModel
from datetime import datetime


class PatientCreate(BaseModel):
    name: str
    phone: str


class PatientResponse(BaseModel):
    id: int
    name: str
    phone: str

    class Config:
        from_attributes = True

class DoctorCreate(BaseModel):
    name: str
    specialty: str


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str

    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_time: datetime
    status: str
    visit_type: str | None
    reason: str | None

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_time: datetime
    status: str
    visit_type: str | None
    reason: str | None

    class Config:
        from_attributes = True

class DepartmentCreate(BaseModel):
    name: str


class DepartmentResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AppointmentDetailResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_time: datetime
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: int | None

class AppointmentFinish(BaseModel):
    visit_type: str
    reason: str