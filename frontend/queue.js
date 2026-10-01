let refreshTimer = null;

async function checkQueue() {
    const id = document.getElementById("appointmentId").value.trim();

    if (!id) {
        alert("Введите номер записи");
        return;
    }

    try {
        const response = await fetch(
            `http://localhost:8000/appointments/${id}/queue-status`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка получения очереди");
        }

        document.getElementById("queueNumber").textContent =
            data.queue_number;

        document.getElementById("currentQueueNumber").textContent =
            data.current_queue_number ?? "-";

        document.getElementById("peopleAhead").textContent =
            data.people_ahead;

        document.getElementById("status").textContent =
            getStatusText(data.status);

        document.getElementById("doctor").textContent =
            data.doctor_name;

        document.getElementById("room").textContent =
            data.room_number || "-";

        // Получаем дополнительные данные записи
        const appointmentResponse = await fetch(
            `http://localhost:8000/appointments/${id}`
        );

        const appointmentData = await appointmentResponse.json();

        document.getElementById("complaint").textContent =
            appointmentData.complaint || "-";

        document.getElementById("department").textContent =
            appointmentData.department_name || "-";

        document.getElementById("result").classList.remove("hidden");

        document.getElementById("lastUpdated").textContent =
            "Обновлено: " + new Date().toLocaleTimeString();

    } catch (error) {
        console.error("QUEUE ERROR:", error);
        alert(error.message);
    }
}


function getStatusText(status) {
    const statuses = {
        BOOKED: "Зарегистрирован",
        ARRIVED: "Пациент пришёл",
        WAITING: "Ожидание",
        IN_PROGRESS: "Приём сейчас",
        COMPLETED: "Приём завершён",
        CANCELLED: "Отменено",
        NO_SHOW: "Не явился"
    };

    return statuses[status] || status;
}


function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    refreshTimer = setInterval(() => {
        const id = document.getElementById("appointmentId").value.trim();

        if (id) {
            checkQueue();
        }
    }, 5000);
}

document.getElementById("appointmentId").addEventListener("change", () => {
    startAutoRefresh();
});

document.getElementById("nextQueueNumber").textContent =
    data.next_queue_number ?? "-";