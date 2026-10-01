import requests
import time
import random


BASE_URL = "http://localhost:8000"



doctors = [

    {
        "id":1,
        "name":"Dr. Ivanov",
        "min_time":5,
        "max_time":12
    },

    {
        "id":2,
        "name":"Dr. Petrov",
        "min_time":8,
        "max_time":15
    },

    {
        "id":3,
        "name":"Dr. Sidorova",
        "min_time":6,
        "max_time":12
    }

]



diagnoses = [

    "Назначено лечение",
    "Требуется дополнительное обследование",
    "Состояние стабильное",
    "Рекомендовано наблюдение",
    "Необходимо повторное посещение"

]


reasons = [

    "Осмотр пациента",
    "Проведена консультация",
    "Жалобы рассмотрены",
    "Даны рекомендации"

]



def finish_patient(appointment_id):


    data = {

        "visit_type":
            random.choice(
                [
                    "Первичный осмотр",
                    "Повторный осмотр"
                ]
            ),

        "reason":
            random.choice(reasons),

        "diagnosis":
            random.choice(diagnoses)

    }



    response = requests.post(

        f"{BASE_URL}/appointments/{appointment_id}/finish",

        json=data

    )


    return response.status_code == 200





def process_doctor(doctor):


    doctor_id = doctor["id"]


    try:


        response = requests.post(

            f"{BASE_URL}/doctors/{doctor_id}/start-next"

        )


        if response.status_code != 200:

            return False



        appointment = response.json()


        appointment_id = appointment["id"]


        priority = appointment.get(
            "priority",
            0
        )


        print(

            f"{doctor['name']} "
            f"started #{appointment_id} "
            f"priority={priority}"

        )



        # пациент не пришёл

        if random.random() < 0.05:


            requests.post(

                f"{BASE_URL}/appointments/{appointment_id}/no-show"

            )


            print(

                f"NO SHOW #{appointment_id}"

            )


            return True




        # время приёма

        duration = random.randint(

            doctor["min_time"],

            doctor["max_time"]

        )


        time.sleep(duration)



        if finish_patient(appointment_id):


            print(

                f"{doctor['name']} "
                f"finished #{appointment_id} "
                f"time={duration}s"

            )



        return True



    except Exception as e:


        print(
            "ERROR:",
            e
        )

        return False





if __name__ == "__main__":


    while True:


        worked = False


        for doctor in doctors:


            result = process_doctor(
                doctor
            )


            if result:

                worked = True




        if not worked:


            print(
                "Queues empty..."
            )


            time.sleep(10)