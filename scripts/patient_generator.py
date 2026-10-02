import requests
import random
import time
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


names = [
    "Ali Karimov",
    "Aziz Tashkent",
    "Bekzod Umarov",
    "Sardor Hasanov",
    "Dilshod Akbarov",
    "Madina Rakhimova",
    "Nodira Karimova",
    "Kamila Yusufova"
]


complaints = [
    "болит сердце",
    "болит голова",
    "боль в спине",
    "температура",
    "боль в суставах",
    "кашель",
    "проблемы со зрением",
    "насморк",
    "головокружение",
    "боль в груди"
]


def generate_patient(index):

    return {
        "name": random.choice(names),
        "phone": f"+998901{random.randint(100000,999999)}",
        "address": "Tashkent",
        "passport_series": f"AUTO{index:06d}",
        "complaint": random.choice(complaints)
    }



def create_patient(index):

    patient = generate_patient(index)

    try:

        # регистрация
        response = requests.post(
            f"{BASE_URL}/registration",
            json=patient
        )


        if response.status_code != 200:
            print(
                "[REGISTER ERROR]",
                response.text
            )
            return


        data = response.json()

        appointment_id = data["appointment"]["id"]

        priority = data["appointment"].get(
            "priority",
            0
        )


        print(
            f"[REGISTER] "
            f"{patient['name']} "
            f"id={appointment_id} "
            f"priority={priority}"
        )


        # пациент пришёл
        arrive = requests.post(
            f"{BASE_URL}/appointments/{appointment_id}/arrive"
        )


        if arrive.status_code != 200:
            print(
                "[ARRIVE ERROR]",
                arrive.text
            )
            return



        # добавить в очередь

        waiting = requests.post(
            f"{BASE_URL}/appointments/{appointment_id}/waiting"
        )


        if waiting.status_code == 200:

            result = waiting.json()

            print(
                f"[WAITING] "
                f"queue={result.get('queue_number')}"
            )

        else:

            print(
                "[WAITING ERROR]",
                waiting.text
            )


    except Exception as e:

        print(
            "[FAILED]",
            e
        )



if __name__ == "__main__":


    total_patients = 100


    for i in range(total_patients):

        create_patient(i)


        # поток пациентов
        time.sleep(
            random.randint(1,3)
        )


    print(
        "Patient generation finished"
    )
