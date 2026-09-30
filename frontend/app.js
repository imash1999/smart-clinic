const form = document.getElementById("registrationForm");
const message = document.getElementById("message");
const result = document.getElementById("result");

form.addEventListener("submit", async function(event) {
    event.preventDefault();

    message.textContent = "Регистрация...";
    result.classList.add("hidden");

    const data = {
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        address: document.getElementById("address").value,
        passport_series: document.getElementById("passport").value,
        complaint: document.getElementById("complaint").value
    };

    try {
        const response = await fetch("http://localhost:8000/registration", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const resultData = await response.json();

        if (!response.ok) {
            throw new Error(resultData.detail || "Ошибка регистрации");
        }

        message.textContent = "";

        document.getElementById("resultName").textContent =
            resultData.patient.name;

        document.getElementById("resultQueue").textContent =
            resultData.appointment.queue_number;

        document.getElementById("resultSpecialty").textContent =
            resultData.specialty;

        document.getElementById("resultStatus").textContent =
            resultData.appointment.status;

        result.classList.remove("hidden");

        form.reset();

    } catch (error) {
        message.textContent = error.message;
    }
});
