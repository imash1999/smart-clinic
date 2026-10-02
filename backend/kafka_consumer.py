import json
import logging

from kafka import KafkaConsumer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


consumer = KafkaConsumer(
    "patient-events",
    bootstrap_servers="kafka:9092",
    group_id="smart-clinic-consumer",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)


logging.info("Consumer started")


for message in consumer:
    logging.info(
        "Received event: %s",
        message.value
    )