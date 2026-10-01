async function loadHistory(){

    const id = document
        .getElementById("patientId")
        .value;


    const response = await fetch(
        `http://localhost:8000/patients/${id}/history`
    );


    const data = await response.json();


    const container =
        document.getElementById("history");


    if(data.length === 0){

        container.innerHTML =
            "<p>История посещений отсутствует</p>";

        return;
    }


    container.innerHTML = data.map(item => `

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
                Тип визита:
                ${item.visit_type || "-"}
            </p>


            <p>
                Результат:
                ${item.reason || "-"}
            </p>


            <p>
                Диагноз:
                ${item.diagnosis || "-"}
            </p>


        </div>

    `).join("");

}