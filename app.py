from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    video_url = data.get("url")
    if not video_url:
        return jsonify({"success": False, "message": "No URL provided"})

    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp4"

    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': output_path,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        return jsonify({
            "success": True,
            "downloadLink": f"/download/{file_id}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/download/<file_id>")
def serve_file(file_id):
    path = f"downloads/{file_id}.mp4"
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)