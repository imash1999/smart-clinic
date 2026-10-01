const API = "http://localhost:8000";


async function loadDashboard(){

    const summaryResponse =
        await fetch(`${API}/analytics/summary`);

    const summary =
        await summaryResponse.json();


    document.getElementById("summary").innerHTML = `

        <div class="result">

            <h2>Общая статистика</h2>

            <p>
                Пациентов:
                <strong>${summary.total_patients}</strong>
            </p>

            <p>
                Всего записей:
                <strong>${summary.total_appointments}</strong>
            </p>

            <p>
                Завершено:
                <strong>${summary.completed}</strong>
            </p>

            <p>
                Ожидают:
                <strong>${summary.waiting}</strong>
            </p>

        </div>

    `;


    const doctorsResponse =
        await fetch(`${API}/analytics/doctors`);

    const doctors =
        await doctorsResponse.json();


    document.getElementById("doctors").innerHTML =
        doctors.map(d => `

        <div class="result">

            <h3>${d.doctor_name}</h3>

            <p>
                Завершённых приёмов:
                ${d.completed_visits}
            </p>

            <p>
                Среднее время:
                ${formatTime(d.average_duration_seconds)}
            </p>

        </div>

    `).join("");



    const departmentsResponse =
        await fetch(`${API}/analytics/departments`);


    const departments =
        await departmentsResponse.json();



        document.getElementById("summary").innerHTML = `

        <h2>Общая статистика</h2>
        
        <div class="cards">
        
        
        <div class="card">
        <h3>Пациенты</h3>
        <div class="number">
        ${summary.total_patients}
        </div>
        </div>
        
        
        <div class="card">
        <h3>Записи</h3>
        <div class="number">
        ${summary.total_appointments}
        </div>
        </div>
        
        
        <div class="card">
        <h3>Завершено</h3>
        <div class="number">
        ${summary.completed}
        </div>
        </div>
        
        
        <div class="card">
        <h3>Ожидают</h3>
        <div class="number">
        ${summary.waiting}
        </div>
        </div>
        
        
        </div>
        
        `;

        new Chart(
            document.getElementById("doctorChart"),
            {
                type: "bar",
        
                data: {
                    labels: doctors.map(
                        d => d.doctor_name
                    ),
        
                    datasets: [
                        {
                            label: "Завершённые приёмы",
        
                            data: doctors.map(
                                d => d.completed_visits
                            )
                        }
                    ]
                }
            }
        );
        
        
        
        new Chart(
            document.getElementById("departmentChart"),
            {
                type: "pie",
        
                data: {
        
                    labels: departments.map(
                        d => d.department_name
                    ),
        
                    datasets: [
                        {
                            label: "Посещения",
        
                            data: departments.map(
                                d => d.total_visits
                            )
                        }
                    ]
                }
            }
        );

}



function formatTime(seconds){

    if(!seconds)
        return "0 мин";


    const minutes =
        Math.round(seconds / 60);


    return minutes + " мин";

}



loadDashboard();