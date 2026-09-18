from flask import Flask, render_template, request, jsonify
import os

from services.traffic_detector import analyze_traffic

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "No video uploaded"
        }), 400

    video = request.files["video"]

    if video.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select a video"
        }), 400

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        video.filename
    )

    video.save(filepath)

    try:
        result = analyze_traffic(filepath)

        os.remove(filepath)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:

        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
