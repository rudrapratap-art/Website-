from flask import Flask, request, render_template_string
import os
import yt_dlp

app = Flask(__name__)

# ====== Save cookies from environment variable ======
COOKIES_FILE = "cookies.txt"
cookies_content = os.environ.get("YOUTUBE_COOKIES")
if cookies_content:
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(cookies_content)
    print("✅ Cookies file saved from environment variable.")
else:
    print("⚠ No cookies found in environment variable YOUTUBE_COOKIES.")

# ====== HTML Template ======
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Direct Link Generator</title>
</head>
<body>
    <h1>Enter YouTube Link</h1>
    <form action="/download" method="post">
        <input type="text" name="url" placeholder="YouTube URL" required>
        <button type="submit">Get Direct Link</button>
    </form>
    {% if video_url %}
        <p><a href="{{ video_url }}" target="_blank">Click here to watch/download</a></p>
    {% elif error %}
        <p style="color:red;">Error: {{ error }}</p>
    {% endif %}
</body>
</html>
"""

# ====== Routes ======
@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_PAGE)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return render_template_string(HTML_PAGE, error="No URL provided")

    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'format': 'best',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")
        return render_template_string(HTML_PAGE, video_url=video_url)

    except Exception as e:
        return render_template_string(HTML_PAGE, error=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
