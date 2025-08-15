from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Video Downloader</title>
<h2>Enter Video Link</h2>
<form action="/download" method="post">
    <input type="text" name="url" placeholder="Paste video URL here" style="width: 400px;" required>
    <br><br>
    <input type="submit" value="Download">
</form>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return "No URL provided!", 400

    video_id = str(uuid.uuid4())
    output_path = f"{video_id}.mp4"

    # yt-dlp options with cookies support
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'cookiefile': 'cookies.txt',  # Use YouTube login cookies
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return f"Error: {str(e)}", 500

    return send_file(output_path, as_attachment=True, download_name="video.mp4")

if __name__ == "__main__":
    # Use Gunicorn in production, only for local test
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
