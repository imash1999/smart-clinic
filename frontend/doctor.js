const doctorId = 2;


async function loadQueue() {

    const queueElement = document.getElementById("queue");
    const message = document.getElementById("message");

    try {

        const response = await fetch(
            `http://localhost:8000/doctors/${doctorId}/queue`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Ошибка загрузки очереди"
            );
        }

        queueElement.innerHTML = "";

        if (data.length === 0) {

            queueElement.innerHTML =
                "<p>Сейчас пациентов в очереди нет.</p>";

        } else {

            data.forEach(appointment => {

                const item = document.createElement("div");

                item.className = "result";

                item.innerHTML = `
                    <h3>№${appointment.queue_number}</h3>

                    <p>
                        <strong>Пациент ID:</strong>
                        ${appointment.patient_id}
                    </p>

                    <p>
                        <strong>Жалоба:</strong>
                        ${appointment.complaint || "-"}
                    </p>

                    <p>
                        <strong>Статус:</strong>
                        ${getStatusText(appointment.status)}
                    </p>

                    <button onclick="startPatient(${appointment.id})">
                        Начать приём
                    </button>
                `;

                queueElement.appendChild(item);
            });
        }

        message.textContent =
            "Обновлено: " + new Date().toLocaleTimeString();

    } catch (error) {

        console.error(error);
        message.textContent = error.message;
    }
}


async function loadCurrentPatient() {

    const currentPatientElement =
        document.getElementById("currentPatient");

    try {

        const response = await fetch(
            `http://localhost:8000/doctors/${doctorId}/current-patient`
        );

        if (response.status === 404) {

            currentPatientElement.innerHTML =
                "<p>Сейчас врач никого не принимает.</p>";

            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Ошибка загрузки пациента"
            );
        }

        currentPatientElement.innerHTML = `
            <div class="result">

                <h2>Текущий пациент</h2>

                <h3>№${data.queue_number}</h3>

                <p>
                    <strong>ФИО:</strong>
                    ${data.patient_name}
                </p>

                <p>
                    <strong>Телефон:</strong>
                    ${data.phone}
                </p>

                <p>
                    <strong>Адрес:</strong>
                    ${data.address || "-"}
                </p>

                <p>
                    <strong>Паспорт:</strong>
                    ${data.passport_series || "-"}
                </p>

                <p>
                    <strong>Жалоба:</strong>
                    ${data.complaint || "-"}
                </p>

                <p>
                    <strong>Статус:</strong>
                    ${getStatusText(data.status)}
                </p>

                <p>
                    <strong>Начало приёма:</strong>
                    ${formatDate(data.started_at)}
                </p>

                <button onclick="showFinishForm(${data.id})">
                    Завершить приём
                </button>

                <div id="finishForm-${data.id}" class="hidden">

                    <label>Тип визита</label>

                    <input
                        type="text"
                        id="visitType-${data.id}"
                        placeholder="Например: Первичный осмотр"
                    >

                    <label>Результат / причина</label>

                    <textarea
                        id="reason-${data.id}"
                        placeholder="Введите результат приёма"
                    ></textarea>

                    <button onclick="finishPatient(${data.id})">
                        Сохранить и завершить
                    </button>

                </div>

            </div>
        `;

    } catch (error) {

        console.error(error);

        currentPatientElement.innerHTML =
            `<p>${error.message}</p>`;
    }
}


async function startPatient(appointmentId) {

    try {

        const response = await fetch(
            `http://localhost:8000/doctors/${doctorId}/start-next`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Не удалось начать приём"
            );
        }

        alert(
            `Приём пациента №${data.queue_number} начат`
        );

        loadQueue();
        loadCurrentPatient();

    } catch (error) {

        console.error(error);
        alert(error.message);
    }
}


function showFinishForm(appointmentId) {

    const form = document.getElementById(
        `finishForm-${appointmentId}`
    );

    form.classList.remove("hidden");
}


async function finishPatient(appointmentId) {

    const visitType = document.getElementById(
        `visitType-${appointmentId}`
    ).value.trim();

    const reason = document.getElementById(
        `reason-${appointmentId}`
    ).value.trim();

    if (!visitType || !reason) {

        alert("Заполните все поля");

        return;
    }

    try {

        const response = await fetch(
            `http://localhost:8000/appointments/${appointmentId}/finish`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    visit_type: visitType,
                    reason: reason
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail || "Не удалось завершить приём"
            );
        }

        alert("Приём завершён");

        loadCurrentPatient();
        loadQueue();

    } catch (error) {

        console.error(error);
        alert(error.message);
    }
}


function getStatusText(status) {

    const statuses = {

        BOOKED: "Зарегистрирован",

        ARRIVED: "Пациент пришёл",

        WAITING: "Ожидает",

        IN_PROGRESS: "Приём сейчас",

        COMPLETED: "Приём завершён",

        CANCELLED: "Отменено",

        NO_SHOW: "Не явился"
    };

    return statuses[status] || status;
}


function formatDate(dateString) {

    if (!dateString) {
        return "-";
    }

    return new Date(dateString).toLocaleString("ru-RU");
}


loadQueue();
loadCurrentPatient();