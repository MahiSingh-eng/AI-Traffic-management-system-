from ultralytics import YOLO
import cv2
import os

# YOLO model
model = YOLO("yolo11n.pt")

# Objects that we consider vehicles
VEHICLE_CLASSES = {
    "car",
    "motorcycle",
    "bus",
    "truck"
}


def analyze_traffic(video_path):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Unable to open video")

    total_vehicle_count = 0
    frames_processed = 0

    vehicle_counts = []

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Process every 5th frame
        if frames_processed % 5 != 0:
            frames_processed += 1
            continue

        results = model(frame, verbose=False)

        current_count = 0

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                if class_name in VEHICLE_CLASSES:
                    current_count += 1

        vehicle_counts.append(current_count)

        total_vehicle_count += current_count

        frames_processed += 1

        # Limit processing for deployment/demo
        if frames_processed >= 300:
            break

    cap.release()

    if not vehicle_counts:
        return {
            "vehicle_count": 0,
            "density": "Low",
            "green_time": 15,
            "status": "Low traffic"
        }

    # Average detected vehicles
    average_count = round(
        sum(vehicle_counts) / len(vehicle_counts)
    )

    # Traffic classification
    if average_count <= 10:

        density = "Low"
        green_time = 15
        status = "Low traffic"

    elif average_count <= 25:

        density = "Medium"
        green_time = 30
        status = "Moderate traffic"

    else:

        density = "High"
        green_time = 60
        status = "Heavy traffic"

    return {
        "vehicle_count": average_count,
        "density": density,
        "green_time": green_time,
        "status": status
    }
