const $ = (id) =>
    document.getElementById(id);


let cameraStream = null;

let cameraInterval = null;

let signalTimer = null;

let trafficChart = null;

let remainingTime = 0;



// ------------------------------------------------
// LOAD INTERSECTIONS
// ------------------------------------------------

async function loadIntersections() {

    const response =
        await fetch(
            "/api/intersections"
        );


    const data =
        await response.json();


    const select =
        $("intersection");


    select.innerHTML =
        data.intersections
            .map(
                intersection => `

                <option
                    value="${intersection.id}">

                    ${intersection.name}
                    —
                    ${intersection.location}

                </option>

                `
            )
            .join("");

}



// ------------------------------------------------
// UPDATE SIGNAL
// ------------------------------------------------

function updateSignal(data) {

    $("vehicles").textContent =
        data.vehicle_count;


    $("density").textContent =
        data.density;


    $("greenTime").textContent =
        data.green_time;


    $("emergency").textContent =

        data.emergency_detected
            ? "YES"
            : "No";


    $("status").textContent =
        data.status;


    $("phase").textContent =
        data.phase;


    remainingTime =
        data.green_time;


    if (
        data.emergency_detected
    ) {

        $("emergencyAlert")
            .classList
            .remove("hidden");

    }

    else {

        $("emergencyAlert")
            .classList
            .add("hidden");

    }


    setSignal(
        data.emergency_detected
            ? "green"
            : "green"
    );


    startCountdown();

}



// ------------------------------------------------
// SIGNAL LIGHT
// ------------------------------------------------

function setSignal(
    signal
) {

    [
        "red",
        "yellow",
        "green"
    ]
    .forEach(
        light => {

            $(light)
                .classList
                .remove(
                    "active"
                );

        }
    );


    $(signal)
        .classList
        .add(
            "active"
        );

}



// ------------------------------------------------
// COUNTDOWN
// ------------------------------------------------

function startCountdown() {

    clearInterval(
        signalTimer
    );


    $("timer")
        .textContent =
        remainingTime + "s";


    signalTimer =
        setInterval(

            () => {

                remainingTime--;


                $("timer")
                    .textContent =
                    remainingTime + "s";


                if (
                    remainingTime <= 0
                ) {

                    clearInterval(
                        signalTimer
                    );

                    cycleSignal();

                }

            },

            1000

        );

}



// ------------------------------------------------
// VISUAL SIGNAL CYCLE
// ------------------------------------------------

function cycleSignal() {

    setSignal("yellow");


    setTimeout(
        () => {

            setSignal("red");

        },
        2000
    );


    setTimeout(
        () => {

            setSignal("green");

        },
        5000
    );

}



// ------------------------------------------------
// CAMERA
// ------------------------------------------------

async function startCamera() {

    try {

        cameraStream =
            await navigator
                .mediaDevices
                .getUserMedia({

                    video: true,

                    audio: false

                });


        $("camera")
            .srcObject =
            cameraStream;


        $("cameraStatus")
            .textContent =
            "Live camera running";


        cameraInterval =
            setInterval(

                analyzeCameraFrame,

                5000

            );


    }

    catch (error) {

        $("cameraStatus")
            .textContent =
            "Camera permission denied";

    }

}



// ------------------------------------------------
// STOP CAMERA
// ------------------------------------------------

function stopCamera() {

    if (
        cameraStream
    ) {

        cameraStream
            .getTracks()
            .forEach(
                track =>
                    track.stop()
            );

    }


    clearInterval(
        cameraInterval
    );


    cameraStream =
        null;


    $("camera")
        .srcObject =
        null;


    $("cameraStatus")
        .textContent =
        "Camera stopped";

}



// ------------------------------------------------
// ANALYZE CAMERA FRAME
// ------------------------------------------------

async function analyzeCameraFrame() {

    if (
        !cameraStream
    ) {

        return;

    }


    const video =
        $("camera");


    if (
        !video.videoWidth
    ) {

        return;

    }


    const canvas =
        $("canvas");


    canvas.width =
        video.videoWidth;


    canvas.height =
        video.videoHeight;


    const context =
        canvas.getContext(
            "2d"
        );


    context.drawImage(

        video,

        0,

        0,

        canvas.width,

        canvas.height

    );


    const image =
        canvas.toDataURL(
            "image/jpeg",
            0.65
        );


    const response =
        await fetch(

            "/api/analyze-frame",

            {

                method:
                    "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body:
                    JSON.stringify({

                        image,

                        intersection_id:
                            $("intersection")
                                .value

                    })

            }

        );


    const data =
        await response.json();


    if (
        data.success
    ) {

        updateSignal(
            data.data
        );

    }

}



// ------------------------------------------------
// VIDEO UPLOAD
// ------------------------------------------------

$("video")
    .addEventListener(

        "change",

        async function () {

            const file =
                this.files[0];


            if (!file) {

                return;

            }


            const formData =
                new FormData();


            formData.append(
                "video",
                file
            );


            formData.append(

                "intersection_id",

                $("intersection")
                    .value

            );


            $("status")
                .textContent =
                "Analyzing video...";


            const response =
                await fetch(

                    "/api/analyze-video",

                    {

                        method:
                            "POST",

                        body:
                            formData

                    }

                );


            const data =
                await response.json();


            if (
                data.success
            ) {

                updateSignal(
                    data.data
                );

                loadDashboard();

            }

            else {

                $("status")
                    .textContent =
                    data.message;

            }

        }

    );



// ------------------------------------------------
// DASHBOARD
// ------------------------------------------------

async function loadDashboard() {

    const response =
        await fetch(
            "/api/dashboard"
        );


    const data =
        await response.json();


    if (
        !data.success
    ) {

        return;

    }


    renderIntersectionCards(
        data.statistics
    );


    renderChart(
        data.recent
    );

}



// ------------------------------------------------
// INTERSECTION CARDS
// ------------------------------------------------

function renderIntersectionCards(
    statistics
) {

    const container =
        $("intersectionCards");


    if (
        !statistics.length
    ) {

        container.innerHTML = `

            <p>
                No traffic data yet.
                Start the camera or upload
                a traffic video.
            </p>

        `;

        return;

    }


    container.innerHTML =
        statistics
            .map(
                item => `

                <div
                    class="intersection">

                    <h3>
                        ${item.name}
                    </h3>

                    <p>
                        Average vehicles:
                        <b>
                            ${item.average_vehicles}
                        </b>
                    </p>

                    <p>
                        Peak vehicles:
                        <b>
                            ${item.maximum_vehicles}
                        </b>
                    </p>

                    <p>
                        Emergency events:
                        <b>
                            ${item.emergency_count}
                        </b>
                    </p>

                </div>

                `
            )
            .join("");

}



// ------------------------------------------------
// CHART
// ------------------------------------------------

function renderChart(
    records
) {

    const reversed =
        [...records].reverse();


    const labels =
        reversed.map(
            row =>
                row.timestamp
                    .slice(11, 19)
        );


    const values =
        reversed.map(
            row =>
                row.vehicle_count
        );


    if (
        trafficChart
    ) {

        trafficChart.destroy();

    }


    trafficChart =
        new Chart(

            $("trafficChart"),

            {

                type:
                    "line",

                data: {

                    labels,

                    datasets: [

                        {

                            label:
                                "Detected Vehicles",

                            data:
                                values,

                            tension:
                                0.25

                        }

                    ]

                },

                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false

                }

            }

        );

}



// ------------------------------------------------
// EVENTS
// ------------------------------------------------

$("startCamera")
    .addEventListener(
        "click",
        startCamera
    );


$("stopCamera")
    .addEventListener(
        "click",
        stopCamera
    );



// ------------------------------------------------
// START
// ------------------------------------------------

loadIntersections();

loadDashboard();


setInterval(
    loadDashboard,
    10000
);
