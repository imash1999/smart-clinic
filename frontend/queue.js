async function checkQueue(){

    const id =
        document.getElementById("appointmentId").value;


    try {

        const response =
            await fetch(
                `http://localhost:8000/appointments/${id}`
            );


        const data =
            await response.json();


        if(!response.ok){
            throw new Error(data.detail);
        }


        document
        .getElementById("queueNumber")
        .textContent =
            data.queue_number;


        document
        .getElementById("status")
        .textContent =
            data.status;


        document
        .getElementById("complaint")
        .textContent =
            data.reason || data.complaint || "-";


        document
        .getElementById("doctor")
        .textContent =
            data.doctor_name;
            
            
        document
        .getElementById("department")
        .textContent =
            data.department_id;
        
        document
        .getElementById("room")
        .textContent =
            data.room_number || "-";

        document
        .getElementById("result")
        .classList
        .remove("hidden");


    }
    catch(error){

        alert(error.message);

    }

}
