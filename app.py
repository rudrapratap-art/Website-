from flask import Flask, render_template_string, request
import os
import yt_dlp

app = Flask(__name__)

# Simple HTML form
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Link Getter</title>
</head>
<body>
    <h2>Enter Video Link</h2>
    <form method="post" action="/getlink">
        <input type="text" name="video_url" placeholder="Paste video link here" style="width:300px;">
        <button type="submit">Get Direct Link</button>
    </form>
    {% if video_link %}
        <h3>Direct Video Link:</h3>
        <a href="{{ video_link }}" target="_blank">{{ video_link }}</a>
    {% elif error %}
        <h3 style="color:red;">Error: {{ error }}</h3>
    {% endif %}
</body>
</html>
"""

def get_direct_link(url):
    # Read cookies from environment variable
    cookies_data = os.environ.get("YOUTUBE_COOKIES", "")
    cookies_path = "cookies.txt"
    with open(cookies_path, "w", encoding="utf-8") as f:
        f.write(cookies_data)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "best",
        "cookies": cookies_path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("url")

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)

@app.route("/getlink", methods=["POST"])
def getlink():
    url = request.form.get("video_url")
    try:
        video_link = get_direct_link(url)
        return render_template_string(HTML_FORM, video_link=video_link)
    except Exception as e:
        return render_template_string(HTML_FORM, error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
