from flask import Flask, request, render_template_string
import yt_dlp

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Instant Video Link</title>
</head>
<body style="font-family: Arial; text-align: center; margin-top: 50px;">
    <h2>Paste Video Link</h2>
    <form action="/download" method="post">
        <input type="text" name="url" placeholder="Enter video link" size="50" required>
        <br><br>
        <button type="submit">Get Direct Link</button>
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
def get_link():
    url = request.form.get("url")
    if not url:
        return render_template_string(HTML_FORM, error="No URL provided!")

    # Only fetch metadata, not download
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "best",
        # Remove cookiefile to avoid requiring login
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get("url")
            if direct_url:
                return render_template_string(HTML_FORM, link=direct_url)
            else:
                return render_template_string(HTML_FORM, error="Could not get direct link.")
    except Exception as e:
        return render_template_string(HTML_FORM, error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
