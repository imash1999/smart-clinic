import json
import logging
from datetime import datetime

from kafka import KafkaProducer


logger = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"


_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    """
    Ленивая инициализация producer'а.
    Создаётся один раз и переиспользуется.
    """
    global _producer

    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
        )

    return _producer


def publish_event(topic: str, event: dict) -> None:
    """
    Публикует событие в Kafka.

    event — обычный dict. Мы добавляем к нему timestamp,
    если его ещё нет, и сериализуем в JSON.
    """
    if "timestamp" not in event:
        event["timestamp"] = datetime.utcnow().isoformat()

    try:
        producer = get_producer()
        producer.send(topic, value=event)
        producer.flush()
        logger.info("Published event to %s: %s", topic, event)
    except Exception as e:
        logger.error("Failed to publish event to %s: %s", topic, e)