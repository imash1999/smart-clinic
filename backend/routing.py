# Определяет специальность врача по жалобе пациента.
# Пока используются простые ключевые слова.
# Позже эту функцию можно заменить ML-моделью.

def determine_specialty(complaint: str) -> str:
    complaint = complaint.lower()

    # Невролог
    if any(word in complaint for word in [
        "голова",
        "головная боль",
        "мигрень",
        "головокружение",
        "нерв",
        "онемение",
        "судороги"
    ]):
        return "Neurologist"

    # Кардиолог
    if any(word in complaint for word in [
        "сердце",
        "грудь",
        "сердцебиение",
        "давление",
        "пульс"
    ]):
        return "Cardiologist"

    # Терапевт
    if any(word in complaint for word in [
        "горло",
        "кашель",
        "температура",
        "насморк",
        "простуда",
        "слабость",
        "боль"
    ]):
        return "Therapist"

    # Если жалоба не подошла ни под одну категорию,
    # направляем пациента к терапевту.
    return "Therapist"