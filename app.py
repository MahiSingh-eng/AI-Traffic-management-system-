from flask import Flask, render_template, request, jsonify, session
from functools import wraps
from datetime import datetime
import sqlite3
import os
import base64
import uuid

from services.traffic_detector import analyze_frame, analyze_video


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

DB_PATH = os.environ.get(
    "DB_PATH",
    "traffic.db"
)

ADMIN_USER = os.environ.get(
    "ADMIN_USER",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)


# --------------------------------------------------
# INTERSECTIONS
# --------------------------------------------------

INTERSECTIONS = [

    {
        "id": 1,
        "name": "Intersection A",
        "location": "Main Road"
    },

    {
        "id": 2,
        "name": "Intersection B",
        "location": "Market Road"
    },

    {
        "id": 3,
        "name": "Intersection C",
        "location": "College Road"
    },

    {
        "id": 4,
        "name": "Intersection D",
        "location": "Station Road"
    }

]


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS traffic_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            intersection_id INTEGER NOT NULL,

            vehicle_count INTEGER NOT NULL,

            density TEXT NOT NULL,

            green_time INTEGER NOT NULL,

            emergency_detected INTEGER NOT NULL DEFAULT 0,

            timestamp TEXT NOT NULL

        )
    """)

    connection.commit()

    connection.close()


initialize_database()


# --------------------------------------------------
# ADMIN AUTHENTICATION
# --------------------------------------------------

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return jsonify({
                "success": False,
                "message": "Admin login required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


@app.post("/api/login")
def login():

    data = request.get_json(
        silent=True
    ) or {}

    username = data.get("username")
    password = data.get("password")

    if (
        username == ADMIN_USER
        and
        password == ADMIN_PASSWORD
    ):

        session["admin"] = True

        return jsonify({
            "success": True
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401


@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


@app.get("/api/me")
def current_user():

    return jsonify({
        "admin": bool(
            session.get("admin")
        )
    })


# --------------------------------------------------
# PAGES
# --------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# --------------------------------------------------
# INTERSECTIONS API
# --------------------------------------------------

@app.get("/api/intersections")
def get_intersections():

    return jsonify({

        "success": True,

        "intersections":
            INTERSECTIONS

    })


# --------------------------------------------------
# SAVE TRAFFIC HISTORY
# --------------------------------------------------

def save_traffic_history(
    intersection_id,
    result
):

    connection = get_db()

    connection.execute(
        """
        INSERT INTO traffic_history
        (
            intersection_id,
            vehicle_count,
            density,
            green_time,
            emergency_detected,
            timestamp
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,

        (
            intersection_id,

            result["vehicle_count"],

            result["density"],

            result["green_time"],

            int(
                result["emergency_detected"]
            ),

            datetime.now().isoformat(
                timespec="seconds"
            )
        )
    )

    connection.commit()

    connection.close()


# --------------------------------------------------
# LIVE CAMERA FRAME
# --------------------------------------------------

@app.post("/api/analyze-frame")
def analyze_live_frame():

    data = request.get_json(
        silent=True
    ) or {}

    image_data = data.get(
        "image"
    )

    intersection_id = int(
        data.get(
            "intersection_id",
            1
        )
    )

    if not image_data:

        return jsonify({
            "success": False,
            "message": "Image is required"
        }), 400


    try:

        if "," in image_data:

            image_data = image_data.split(
                ",",
                1
            )[1]


        image_bytes = base64.b64decode(
            image_data
        )


        result = analyze_frame(
            image_bytes
        )


        save_traffic_history(
            intersection_id,
            result
        )


        return jsonify({

            "success": True,

            "data": result

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


# --------------------------------------------------
# VIDEO ANALYSIS
# --------------------------------------------------

@app.post("/api/analyze-video")
def analyze_uploaded_video():

    video = request.files.get(
        "video"
    )

    intersection_id = int(
        request.form.get(
            "intersection_id",
            1
        )
    )


    if not video:

        return jsonify({

            "success": False,

            "message":
                "Video is required"

        }), 400


    temporary_file = os.path.join(

        "/tmp",

        f"traffic_{uuid.uuid4().hex}.mp4"

    )


    video.save(
        temporary_file
    )


    try:

        result = analyze_video(
            temporary_file
        )


        save_traffic_history(
            intersection_id,
            result
        )


        return jsonify({

            "success": True,

            "data": result

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500


    finally:

        if os.path.exists(
            temporary_file
        ):

            os.remove(
                temporary_file
            )


# --------------------------------------------------
# DASHBOARD DATA
# --------------------------------------------------

@app.get("/api/dashboard")
def dashboard():

    connection = get_db()


    statistics = connection.execute(
        """
        SELECT

            intersection_id,

            AVG(vehicle_count)
                AS average_vehicles,

            MAX(vehicle_count)
                AS maximum_vehicles,

            SUM(emergency_detected)
                AS emergency_count,

            COUNT(*)
                AS sample_count

        FROM traffic_history

        WHERE timestamp >=
            datetime(
                'now',
                '-24 hours'
            )

        GROUP BY intersection_id

        """
    ).fetchall()


    recent = connection.execute(
        """
        SELECT *

        FROM traffic_history

        ORDER BY id DESC

        LIMIT 50
        """
    ).fetchall()


    connection.close()


    result = []


    for row in statistics:

        intersection_id = int(
            row["intersection_id"]
        )


        intersection = next(

            (
                item

                for item in INTERSECTIONS

                if item["id"]
                ==
                intersection_id

            ),

            None

        )


        result.append({

            "intersection_id":
                intersection_id,

            "name":
                intersection["name"]
                if intersection
                else "Unknown",

            "average_vehicles":
                round(
                    row[
                        "average_vehicles"
                    ] or 0,
                    1
                ),

            "maximum_vehicles":
                int(
                    row[
                        "maximum_vehicles"
                    ] or 0
                ),

            "emergency_count":
                int(
                    row[
                        "emergency_count"
                    ] or 0
                ),

            "sample_count":
                int(
                    row[
                        "sample_count"
                    ] or 0
                )

        })


    return jsonify({

        "success": True,

        "statistics": result,

        "recent":
            [
                dict(row)
                for row in recent
            ]

    })


# --------------------------------------------------
# ADMIN HISTORY
# --------------------------------------------------

@app.get("/api/history")
@admin_required
def history():

    connection = get_db()


    rows = connection.execute(
        """
        SELECT *

        FROM traffic_history

        ORDER BY id DESC

        LIMIT 500
        """
    ).fetchall()


    connection.close()


    return jsonify({

        "success": True,

        "history":
            [
                dict(row)
                for row in rows
            ]

    })


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
