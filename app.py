from flask import Flask, request, render_template_string, send_from_directory, jsonify, abort
import os
import yt_dlp
import uuid

app = Flask(__name__)

# Create downloads folder
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Store progress in memory
progress_data = {}

COOKIES_FILE = "cookies.txt"
cookies_content = os.environ.get("YOUTUBE_COOKIES")
if cookies_content:
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(cookies_content)

# ====== HTML Template ======
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <script>
        function checkProgress(task_id) {
            fetch('/progress/' + task_id)
            .then(response => response.json())
            .then(data => {
                if (data.status === "downloading") {
                    document.getElementById("progress").value = data.percent;
                    setTimeout(() => checkProgress(task_id), 1000);
                } else if (data.status === "finished") {
                    document.getElementById("progress").value = 100;
                    document.getElementById("download-link").innerHTML = 
                        '<a href="' + data.url + '" target="_blank">⬇ Download Ready</a>';
                } else if (data.status === "error") {
                    document.getElementById("download-link").innerHTML = 
                        '<p style="color:red;">Error: ' + data.error + '</p>';
                }
            });
        }
    </script>
</head>
<body>
    <h1>YouTube Downloader</h1>
    <form action="/formats" method="post">
        <input type="text" name="url" placeholder="YouTube URL" required>
        <button type="submit">Get Formats</button>
    </form>

    {% if formats %}
        <h2>Choose Format</h2>
        <form action="/download" method="post">
            <input type="hidden" name="url" value="{{ url }}">
            <select name="format_id" required>
                {% for f in formats %}
                    <option value="{{ f['format_id'] }}">
                        {{ f['format_id'] }} | {{ f['ext'] }} | {{ f['resolution'] or f['asr'] or '' }} | {{ f['filesize']|default('') }}
                    </option>
                {% endfor %}
            </select>
            <button type="submit">Download</button>
        </form>
    {% endif %}

    {% if task_id %}
        <h2>Download Progress</h2>
        <progress id="progress" value="0" max="100"></progress>
        <div id="download-link"></div>
        <script>checkProgress("{{ task_id }}");</script>
    {% endif %}

    {% if error %}
        <p style="color:red;">Error: {{ error }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_PAGE)

@app.route("/formats", methods=["POST"])
def formats():
    url = request.form.get("url")
    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
        return render_template_string(HTML_PAGE, formats=formats, url=url)
    except Exception as e:
        return render_template_string(HTML_PAGE, error=str(e))

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    format_id = request.form.get("format_id")
    task_id = str(uuid.uuid4())
    progress_data[task_id] = {"status": "downloading", "percent": 0}

    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '').strip()
            progress_data[task_id]["percent"] = float(percent)
        elif d['status'] == 'finished':
            progress_data[task_id]["status"] = "merging"

    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'format': format_id + "+bestaudio/best",
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'progress_hooks': [hook],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            downloaded_file = ydl.prepare_filename(info)
            if not downloaded_file.endswith(".mp4"):
                downloaded_file = downloaded_file.rsplit(".", 1)[0] + ".mp4"
            base_name = os.path.basename(downloaded_file)

        progress_data[task_id] = {
            "status": "finished",
            "url": f"/files/{base_name}"
        }

        return render_template_string(HTML_PAGE, task_id=task_id)
    except Exception as e:
        progress_data[task_id] = {"status": "error", "error": str(e)}
        return render_template_string(HTML_PAGE, error=str(e))

@app.route("/progress/<task_id>")
def progress(task_id):
    return jsonify(progress_data.get(task_id, {"status": "error", "error": "Invalid task id"}))

@app.route("/files/<path:filename>")
def serve_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404)

    response = send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

    # Auto-delete after sending (one-time link)
    try:
        os.remove(file_path)
    except Exception:
        pass

    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
