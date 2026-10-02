import json
import logging
from datetime import datetime
from collections import Counter

from kafka import KafkaConsumer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


TOPICS = [
    "patient-events",
    "queue-events",
    "consultation-events",
    "appointment-events",
]


consumer = KafkaConsumer(
    *TOPICS,
    bootstrap_servers="kafka:9092",
    group_id="smart-clinic-analytics",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

waiting_started = {}
waiting_times = []
consultation_times = []
patients_by_doctor = Counter()
patients_by_department = Counter()
patients_by_hour = Counter()
no_show_count = 0
current_queue_size = 0
max_queue_size = 0
counted_patients = set()

def parse_datetime(value):
    """Convert ISO timestamp to datetime."""

    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def print_metrics():

    average_waiting = (
        sum(waiting_times) / len(waiting_times)
        if waiting_times
        else 0
    )

    average_consultation = (
        sum(consultation_times) / len(consultation_times)
        if consultation_times
        else 0
    )

    logging.info(
        "\n"
        "========== ANALYTICS ==========\n"
        "Average waiting time: %.2f sec\n"
        "Average consultation time: %.2f sec\n"
        "Patients by doctor: %s\n"
        "Patients by department: %s\n"
        "No-show: %d\n"
        "Patients by hour: %s\n"
        "Current queue size: %d\n"
        "Maximum queue size: %d\n"
        "================================",
        average_waiting,
        average_consultation,
        dict(patients_by_doctor),
        dict(patients_by_department),
        no_show_count,
        dict(patients_by_hour),
        current_queue_size,
        max_queue_size,
    )


logging.info("Analytics consumer started")
logging.info("Topics: %s", ", ".join(TOPICS))

for message in consumer:

    event = message.value

    event_type = event.get("event_type")
    appointment_id = event.get("appointment_id")

    timestamp = parse_datetime(event.get("timestamp"))

    if timestamp is None:
        logging.warning(
            "Event without valid timestamp: %s",
            event
        )
        continue

    if event_type == "patient_registered":

        if appointment_id not in counted_patients:

            counted_patients.add(appointment_id)

            doctor_id = event.get("doctor_id")
            department_id = event.get("department_id")

            if doctor_id is not None:
                patients_by_doctor[doctor_id] += 1

            if department_id is not None:
                patients_by_department[department_id] += 1

            patients_by_hour[timestamp.hour] += 1

    elif event_type == "appointment_waiting":

        # Remember when this appointment entered the queue
        waiting_started[appointment_id] = timestamp

        current_queue_size += 1

        max_queue_size = max(
            max_queue_size,
            current_queue_size
        )

    elif event_type == "appointment_started":

        # Patient leaves waiting queue
        if current_queue_size > 0:
            current_queue_size -= 1


        # Calculate waiting time
        waiting_time = waiting_started.pop(
            appointment_id,
            None
        )

        if waiting_time is not None:

            wait_seconds = (
                timestamp - waiting_time
            ).total_seconds()

            if wait_seconds >= 0:

                waiting_times.append(
                    wait_seconds
                )

    elif event_type == "appointment_finished":

        started_at = parse_datetime(
            event.get("started_at")
        )

        finished_at = parse_datetime(
            event.get("finished_at")
        )

        if started_at and finished_at:

            consultation_seconds = (
                finished_at - started_at
            ).total_seconds()

            if consultation_seconds >= 0:

                consultation_times.append(
                    consultation_seconds
                )

    elif event_type == "appointment_no_show":

        no_show_count += 1

    if event_type in {
        "appointment_started",
        "appointment_finished",
        "appointment_no_show",
    }:

        print_metrics()