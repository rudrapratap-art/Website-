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

# ====== HTML Template (Premium Glass-Morphism UI) ======
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>🎥 YouTube Direct Link Generator</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');
        
        :root {
            --youtube-red: #ff0000;
            --youtube-red-hover: #cc0000;
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-border: rgba(255, 255, 255, 0.18);
            --text-shadow: 0 2px 4px rgba(0,0,0,0.25);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            background-attachment: fixed;
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }
        
        body::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 10% 20%, rgba(255, 0, 0, 0.05) 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, rgba(0, 100, 255, 0.05) 0%, transparent 20%);
            pointer-events: none;
            z-index: -1;
        }
        
        .container {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 32px;
            width: 100%;
            max-width: 520px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 15px rgba(255, 0, 0, 0.1);
            transform: translateY(0);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .container:hover {
            transform: translateY(-5px);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.4),
                0 0 25px rgba(255, 0, 0, 0.15);
        }
        
        .header {
            text-align: center;
            margin-bottom: 28px;
            position: relative;
        }
        
        h1 {
            font-size: 2.2rem;
            font-weight: 600;
            margin-bottom: 12px;
            background: linear-gradient(90deg, #ff0000, #ff5e5e);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: var(--text-shadow);
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.05rem;
            max-width: 400px;
            margin: 0 auto;
            line-height: 1.5;
        }
        
        form {
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .input-group {
            position: relative;
        }
        
        .input-group::after {
            content: '🔗';
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(255, 255, 255, 0.6);
            font-size: 1.1rem;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 16px 20px 16px 45px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 1.05rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: rgba(255, 0, 0, 0.4);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.2);
        }
        
        input[type="text"]::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        button {
            padding: 16px;
            background: linear-gradient(90deg, var(--youtube-red), #e60000);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 1.1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(255, 0, 0, 0.3);
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            position: relative;
            overflow: hidden;
        }
        
        button:hover {
            background: linear-gradient(90deg, var(--youtube-red-hover), #b30000);
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255, 0, 0, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -60%;
            width: 20px;
            height: 200%;
            background: rgba(255, 255, 255, 0.2);
            transform: rotate(30deg);
            transition: all 0.6s;
        }
        
        button:hover::after {
            left: 120%;
        }
        
        .result, .error {
            padding: 20px;
            border-radius: 16px;
            margin-top: 20px;
            animation: fadeIn 0.4s ease;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .result {
            background: rgba(0, 150, 0, 0.1);
            border-left: 3px solid #4CAF50;
        }
        
        .error {
            background: rgba(255, 0, 0, 0.1);
            border-left: 3px solid var(--youtube-red);
        }
        
        a {
            color: #4fc3f7;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        a:hover {
            color: #81d4fa;
            text-decoration: underline;
        }
        
        a::after {
            content: '→';
            margin-left: 4px;
            transition: transform 0.2s;
        }
        
        a:hover::after {
            transform: translateX(3px);
        }
        
        .youtube-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--youtube-red);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            margin-right: 8px;
            font-weight: bold;
            font-size: 0.8rem;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 24px 20px;
            }
            
            h1 {
                font-size: 1.8rem;
            }
            
            button {
                padding: 14px;
                font-size: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="youtube-icon">YT</span> Direct Link Generator</h1>
            <p class="subtitle">Get high-quality direct video links from YouTube without downloading</p>
        </div>
        
        <form action="/download" method="post">
            <div class="input-group">
                <input type="text" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            <button type="submit">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19 13H13V11H19V13ZM5 11H8.99V13H5V11Z" fill="white"/>
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L15 12L10 7V17Z" fill="white"/>
                </svg>
                Generate Direct Link
            </button>
        </form>

        {% if video_url %}
            <div class="result">
                <p>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 6px;">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="#4CAF50"/>
                    </svg>
                    Direct video link generated successfully
                </p>
                <p style="margin-top: 12px;"><a href="{{ video_url }}" target="_blank">Play video now <span style="display: inline-block; transition: transform 0.2s;">→</span></a></p>
            </div>
        {% elif error %}
            <div class="error">
                <p>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 6px;">
                        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="var(--youtube-red)"/>
                    </svg>
                    {{ error }}
                </p>
            </div>
        {% endif %}
    </div>
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
