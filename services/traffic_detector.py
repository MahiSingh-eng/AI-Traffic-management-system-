from ultralytics import YOLO

import cv2
import numpy as np

import os


MODEL_NAME = os.environ.get(
    "YOLO_MODEL",
    "yolo11n.pt"
)


model = YOLO(
    MODEL_NAME
)


# --------------------------------------------------
# VEHICLE CLASSES
# --------------------------------------------------

VEHICLE_CLASSES = {

    "car",

    "motorcycle",

    "bus",

    "truck"

}


# --------------------------------------------------
# EMERGENCY VEHICLES
# --------------------------------------------------

EMERGENCY_CLASSES = {

    "ambulance",

    "fire_truck",

    "police_car",

    "emergency_vehicle"

}


# --------------------------------------------------
# SIGNAL DECISION
# --------------------------------------------------

def calculate_signal_plan(
    vehicle_count,
    emergency=False
):

    # Emergency priority

    if emergency:

        return {

            "density":
                "Emergency Priority",

            "green_time":
                75,

            "status":
                "Emergency vehicle detected",

            "phase":
                "Priority"

        }


    # Low traffic

    if vehicle_count <= 10:

        return {

            "density":
                "Low",

            "green_time":
                15,

            "status":
                "Low traffic",

            "phase":
                "Green"

        }


    # Medium traffic

    if vehicle_count <= 25:

        return {

            "density":
                "Medium",

            "green_time":
                30,

            "status":
                "Moderate traffic",

            "phase":
                "Green"

        }


    # High traffic

    return {

        "density":
            "High",

        "green_time":
            60,

        "status":
            "Heavy traffic",

        "phase":
            "Green"

    }


# --------------------------------------------------
# ANALYZE IMAGE
# --------------------------------------------------

def analyze_frame(
    raw_bytes
):

    image_array = np.frombuffer(

        raw_bytes,

        np.uint8

    )


    frame = cv2.imdecode(

        image_array,

        cv2.IMREAD_COLOR

    )


    if frame is None:

        raise ValueError(
            "Invalid image"
        )


    results = model(

        frame,

        verbose=False

    )


    vehicle_count = 0

    emergency_detected = False

    detected_objects = []


    for result in results:

        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )


            class_name = str(

                model.names[
                    class_id
                ]

            ).lower()


            if class_name in VEHICLE_CLASSES:

                vehicle_count += 1

                detected_objects.append(
                    class_name
                )


            if class_name in EMERGENCY_CLASSES:

                emergency_detected = True

                detected_objects.append(
                    class_name
                )


    signal = calculate_signal_plan(

        vehicle_count,

        emergency_detected

    )


    return {

        "vehicle_count":
            vehicle_count,

        "emergency_detected":
            emergency_detected,

        "detected_objects":
            detected_objects,

        **signal

    }


# --------------------------------------------------
# ANALYZE VIDEO
# --------------------------------------------------

def analyze_video(
    video_path
):

    capture = cv2.VideoCapture(
        video_path
    )


    if not capture.isOpened():

        raise ValueError(
            "Unable to open video"
        )


    counts = []

    emergency_detected = False

    frame_number = 0


    while True:

        success, frame = capture.read()


        if not success:

            break


        # Process every fifth frame

        if frame_number % 5 == 0:

            results = model(

                frame,

                verbose=False

            )


            count = 0


            for result in results:

                for box in result.boxes:

                    class_id = int(
                        box.cls[0]
                    )


                    class_name = str(

                        model.names[
                            class_id
                        ]

                    ).lower()


                    if class_name in VEHICLE_CLASSES:

                        count += 1


                    if class_name in EMERGENCY_CLASSES:

                        emergency_detected = True


            counts.append(
                count
            )


        frame_number += 1


        # Limit demo processing

        if frame_number >= 300:

            break


    capture.release()


    average_count = (

        round(
            sum(counts)
            /
            len(counts)
        )

        if counts

        else 0

    )


    signal = calculate_signal_plan(

        average_count,

        emergency_detected

    )


    return {

        "vehicle_count":
            average_count,

        "emergency_detected":
            emergency_detected,

        "detected_objects":
            [],

        **signal

    }
