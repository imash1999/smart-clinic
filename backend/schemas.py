from pydantic import BaseModel
from datetime import datetime


class PatientCreate(BaseModel):
    name: str
    phone: str
    address: str | None = None
    passport_series: str | None = None


class PatientResponse(BaseModel):
    id: int
    name: str
    phone: str
    address: str | None
    passport_series: str | None

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


class DepartmentCreate(BaseModel):
    name: str


class DepartmentResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_time: datetime
    status: str
    visit_type: str | None = None
    reason: str | None = None
    complaint: str | None = None
    queue_number: int | None = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_time: datetime
    status: str
    queue_number: int | None
    complaint: str | None
    started_at: datetime | None
    finished_at: datetime | None
    visit_type: str | None
    reason: str | None

    class Config:
        from_attributes = True


class AppointmentDetailResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    doctor_name: str
    room_number: str | None
    department_name: str
    department_id: int
    appointment_time: datetime
    status: str
    queue_number: int | None
    complaint: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: int | None
    visit_type: str | None
    reason: str | None

    class Config:
        from_attributes = True


class AppointmentFinish(BaseModel):
    visit_type: str
    reason: str


class AppointmentFinishResponse(BaseModel):
    finished: AppointmentResponse
    next_patient: AppointmentResponse | None

class RegistrationCreate(BaseModel):
    name: str
    phone: str
    address: str
    passport_series: str
    complaint: str


class RegistrationResponse(BaseModel):
    patient: PatientResponse
    appointment: AppointmentResponse
    specialty: str