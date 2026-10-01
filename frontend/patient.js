async function searchPatient(){

    const phone =
        document.getElementById("phone").value.trim();


    const url = new URL(
        "http://localhost:8000/patients/search"
    );

    url.searchParams.append("phone", phone);


    const response = await fetch(url);


    const patient =
        await response.json();


    if(!response.ok){

        alert(patient.detail);
        return;

    }


    document.getElementById(
        "patientInfo"
    ).innerHTML = `

    <div class="result">

        <h2>
            ${patient.name}
        </h2>


        <p>
            Телефон:
            ${patient.phone}
        </p>


        <p>
            Паспорт:
            ${patient.passport_series || "-"}
        </p>


        <h2>
            История посещений
        </h2>


        <div id="history">
            Загрузка...
        </div>


    </div>

    `;


    loadHistory(patient.id);

}


async function loadHistory(id){

    const response =
        await fetch(
        `http://localhost:8000/patients/${id}/history`
        );


    const data =
        await response.json();


    const history =
        document.getElementById("history");


    if(data.length === 0){

        history.innerHTML =
            "<p>Нет завершённых посещений</p>";

        return;

    }


    history.innerHTML = data.map(item => `

        <div class="result">

            <h3>
                Посещение №${item.id}
            </h3>


            <p>
                Дата:
                ${new Date(item.finished_at)
                .toLocaleString()}
            </p>


            <p>
                Жалоба:
                ${item.complaint || "-"}
            </p>


            <p>
                Врач:
                ${item.doctor_name || "-"}
            </p>

            <p>
                Отделение:
                ${item.department_name || "-"}
            </p>


            <p>
                Диагноз:
                ${item.diagnosis || "-"}
            </p>


            <p>
                Результат:
                ${item.reason || "-"}
            </p>


        </div>

    `).join("");

}