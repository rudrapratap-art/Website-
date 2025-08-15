from flask import Flask, request, render_template_string
import yt_dlp

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Downloader</title>
</head>
<body style="font-family: Arial; text-align: center; margin-top: 50px;">
    <h2>Paste Video Link</h2>
    <form action="/download" method="post">
        <input type="text" name="url" placeholder="Enter video link" size="50" required>
        <br><br>
        <button type="submit">Get Download Link</button>
    </form>
    {% if link %}
        <h3>Direct Download Link:</h3>
        <a href="{{ link }}" target="_blank">{{ link }}</a>
    {% elif error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return render_template_string(HTML_FORM, error="No URL provided!")

    ydl_opts = {
        'format': 'best',  # You can change to 'bestvideo+bestaudio'
        'quiet': True,
        'cookiefile': 'cookies.txt',  # Use cookies for YouTube login bypass
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get("url")
            return render_template_string(HTML_FORM, link=direct_url)
    except Exception as e:
        return render_template_string(HTML_FORM, error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
