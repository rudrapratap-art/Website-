from flask import Flask, request, render_template_string
import os
import yt_dlp

app = Flask(__name__)

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
    <title>YouTube Direct Link Generator</title>
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

    {% if video_url %}
        <p><a href="{{ video_url }}" target="_blank">Download Ready</a></p>
    {% elif error %}
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
            'listformats': True,
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
    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'format': format_id + "+bestaudio/best",
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_url = info.get("requested_downloads", [{}])[0].get("filepath", "")
        return render_template_string(HTML_PAGE, video_url=video_url)
    except Exception as e:
        return render_template_string(HTML_PAGE, error=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
