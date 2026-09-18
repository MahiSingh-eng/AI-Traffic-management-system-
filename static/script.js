const form = document.getElementById("uploadForm");

const loading = document.getElementById("loading");

const dashboard = document.getElementById("dashboard");

const vehicleCount =
    document.getElementById("vehicleCount");

const density =
    document.getElementById("density");

const greenTime =
    document.getElementById("greenTime");

const status =
    document.getElementById("status");


form.addEventListener("submit", async function(event) {

    event.preventDefault();

    const video =
        document.getElementById("video").files[0];

    if (!video) {
        alert("Please select a video.");
        return;
    }

    const formData = new FormData();

    formData.append("video", video);

    loading.classList.remove("hidden");

    dashboard.classList.add("hidden");

    try {

        const response = await fetch(
            "/analyze",
            {
                method: "POST",
                body: formData
            }
        );

        const result = await response.json();

        if (!result.success) {

            alert(result.message);

            return;
        }

        const data = result.data;

        vehicleCount.textContent =
            data.vehicle_count;

        density.textContent =
            data.density;

        greenTime.textContent =
            data.green_time;

        status.textContent =
            data.status;

        dashboard.classList.remove("hidden");

    } catch (error) {

        alert(
            "Something went wrong while analyzing the video."
        );

        console.error(error);

    } finally {

        loading.classList.add("hidden");

    }

});
