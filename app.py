from flask import Flask, request, render_template_string, send_file, make_response
import os
import yt_dlp
import subprocess
import uuid
import threading
import time

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

# ====== HTML Templates ======
HOME_PAGE = """
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
        
        <form action="/get-formats" method="post">
            <div class="input-group">
                <input type="text" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            <button type="submit">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19 13H13V11H19V13ZM5 11H8.99V13H5V11Z" fill="white"/>
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L15 12L10 7V17Z" fill="white"/>
                </svg>
                Show Available Formats
            </button>
        </form>

        {% if error %}
            <div class="error">
                <p>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 6px;">
                        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="var(--youtube-red)"/>
                    </svg>
                    {{ error }}
                </p>
            </div>
        {% endif %}
        
        {% if video_url %}
            <div class="result">
                <p>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 6px;">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="#4CAF50"/>
                    </svg>
                    Video ready! Click below to download.
                </p>
                <p style="margin-top: 12px;">
                    <a href="{{ video_url }}" target="_blank">⬇️ Download Merged Video</a>
                </p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

FORMATS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>🎥 Select Video Format</title>
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
            max-width: 700px;
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
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.5;
            margin-bottom: 24px;
        }
        
        .format-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .format-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .format-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-3px);
        }
        
        .format-card.selected {
            border-color: var(--youtube-red);
            background: rgba(255, 0, 0, 0.1);
            box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.2);
        }
        
        .format-type {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .video-type {
            background: rgba(0, 150, 0, 0.2);
            color: #81C784;
        }
        
        .audio-type {
            background: rgba(0, 100, 255, 0.2);
            color: #64B5F6;
        }
        
        .format-resolution {
            font-weight: 600;
            font-size: 1.1rem;
            margin: 8px 0;
            color: #fff;
        }
        
        .format-details {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .format-id {
            background: rgba(255, 255, 255, 0.1);
            padding: 3px 8px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
            margin-top: 8px;
            display: inline-block;
        }
        
        .controls {
            display: flex;
            gap: 16px;
            margin-top: 24px;
        }
        
        .btn {
            flex: 1;
            padding: 14px;
            border-radius: 14px;
            font-size: 1.05rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .btn-back {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .btn-back:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .btn-download {
            background: linear-gradient(90deg, var(--youtube-red), #e60000);
            color: white;
        }
        
        .btn-download:hover {
            background: linear-gradient(90deg, var(--youtube-red-hover), #b30000);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
        }
        
        .btn-download:disabled {
            background: rgba(128, 128, 128, 0.5);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .selection-summary {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
            display: none;
        }
        
        .summary-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .summary-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .summary-label {
            color: rgba(255, 255, 255, 0.7);
        }
        
        .summary-value {
            font-weight: 500;
        }
        
        .error {
            padding: 20px;
            border-radius: 16px;
            margin-top: 20px;
            animation: fadeIn 0.4s ease;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 0, 0, 0.3);
            background: rgba(255, 0, 0, 0.1);
            border-left: 3px solid var(--youtube-red);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 600px) {
            .format-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span style="display: inline-flex; align-items: center; justify-content: center; background: var(--youtube-red); color: white; width: 28px; height: 28px; border-radius: 50%; margin-right: 8px; font-weight: bold; font-size: 0.8rem;">YT</span> Format Selection</h1>
            <p class="subtitle">Select your preferred video and audio quality. We'll merge them for the best experience.</p>
        </div>
        
        <form id="formatForm" action="/download" method="post">
            <input type="hidden" name="url" value="{{ url }}">
            <input type="hidden" name="video_format" id="videoFormatInput">
            <input type="hidden" name="audio_format" id="audioFormatInput">
            
            <div class="format-grid">
                {% for f in formats %}
                    <div class="format-card" 
                         data-type="{{ f.type }}" 
                         data-id="{{ f.format_id }}"
                         data-resolution="{{ f.resolution }}"
                         data-ext="{{ f.ext }}"
                         data-note="{{ f.format_note }}"
                         data-bitrate="{{ f.tbr|round(1) if f.tbr else 'N/A' }}">
                        <span class="format-type {{ f.type }}-type">{{ f.type|upper }}</span>
                        <div class="format-resolution">
                            {% if f.resolution %}{{ f.resolution }}{% else %}{{ f.format_note }}{% endif %}
                        </div>
                        <div class="format-details">
                            {% if f.vcodec and f.vcodec != 'none' %}Video: {{ f.vcodec }}{% endif %}
                            {% if f.acodec and f.acodec != 'none' %}<br>Audio: {{ f.acodec }}{% endif %}
                            {% if f.tbr %}<br>Bitrate: {{ f.tbr|round(1) }} kbps{% endif %}
                            {% if f.filesize %}
                              <br>Size: 
                              {% set size = f.filesize %}
                              {% if size < 1024 %}
                                {{ size }} B
                              {% elif size < 1048576 %}
                                {{ '%.1f'|format(size / 1024) }} KB
                              {% elif size < 1073741824 %}
                                {{ '%.1f'|format(size / 1048576) }} MB
                              {% else %}
                                {{ '%.1f'|format(size / 1073741824) }} GB
                              {% endif %}
                            {% endif %}
                        </div>
                        <span class="format-id">ID: {{ f.format_id }}</span>
                    </div>
                {% endfor %}
            </div>
            
            <div class="selection-summary" id="selectionSummary">
                <div class="summary-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="#4CAF50"/>
                    </svg>
                    Selected Formats
                </div>
                <div class="summary-item">
                    <span class="summary-label">Video Format:</span>
                    <span class="summary-value" id="videoSummary">Not selected</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Audio Format:</span>
                    <span class="summary-value" id="audioSummary">Not selected</span>
                </div>
            </div>
            
            {% if error %}
                <div class="error">
                    <p>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 6px;">
                            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="var(--youtube-red)"/>
                        </svg>
                        {{ error }}
                    </p>
                </div>
            {% endif %}
            
            <div class="controls">
                <button type="button" class="btn btn-back" onclick="window.history.back()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M15 19l-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Back
                </button>
                <button type="submit" class="btn btn-download" id="downloadBtn" disabled>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Generate Merged Video
                </button>
            </div>
        </form>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const formatCards = document.querySelectorAll('.format-card');
            const videoFormatInput = document.getElementById('videoFormatInput');
            const audioFormatInput = document.getElementById('audioFormatInput');
            const downloadBtn = document.getElementById('downloadBtn');
            const selectionSummary = document.getElementById('selectionSummary');
            const videoSummary = document.getElementById('videoSummary');
            const audioSummary = document.getElementById('audioSummary');
            
            let selectedVideo = null;
            let selectedAudio = null;
            
            formatCards.forEach(card => {
                card.addEventListener('click', function() {
                    const type = this.getAttribute('data-type');
                    const id = this.getAttribute('data-id');
                    const resolution = this.getAttribute('data-resolution') || this.getAttribute('data-note');
                    const ext = this.getAttribute('data-ext');
                    
                    if (type === 'video') {
                        document.querySelectorAll('.format-card[data-type="video"].selected').forEach(v => {
                            v.classList.remove('selected');
                        });
                        
                        this.classList.add('selected');
                        selectedVideo = id;
                        videoFormatInput.value = id;
                        videoSummary.textContent = `${resolution} (${ext})`;
                    } else if (type === 'audio') {
                        document.querySelectorAll('.format-card[data-type="audio"].selected').forEach(a => {
                            a.classList.remove('selected');
                        });
                        
                        this.classList.add('selected');
                        selectedAudio = id;
                        audioFormatInput.value = id;
                        audioSummary.textContent = `${this.getAttribute('data-note') || 'Audio'} (${ext})`;
                    }
                    
                    if (selectedVideo && selectedAudio) {
                        downloadBtn.disabled = false;
                        selectionSummary.style.display = 'block';
                    } else {
                        downloadBtn.disabled = true;
                        selectionSummary.style.display = selectedVideo || selectedAudio ? 'block' : 'none';
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

# ====== Routes ======
@app.route("/", methods=["GET"])
def home():
    return render_template_string(HOME_PAGE)

@app.route("/get-formats", methods=["POST"])
def get_formats():
    url = request.form.get("url")
    if not url:
        return render_template_string(HOME_PAGE, error="No URL provided")

    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            
            processed_formats = []
            for f in formats:
                if 'vcodec' not in f and 'acodec' not in f:
                    continue
                
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    f_type = 'video'
                elif f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    f_type = 'video'
                elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    f_type = 'audio'
                else:
                    continue
                
                processed_formats.append({
                    'format_id': f.get('format_id', ''),
                    'resolution': f.get('resolution', ''),
                    'ext': f.get('ext', ''),
                    'format_note': f.get('format_note', ''),
                    'vcodec': f.get('vcodec', 'none'),
                    'acodec': f.get('acodec', 'none'),
                    'tbr': f.get('tbr', 0),
                    'filesize': f.get('filesize', None),
                    'type': f_type
                })
            
            video_formats = [f for f in processed_formats if f['type'] == 'video']
            audio_formats = [f for f in processed_formats if f['type'] == 'audio']
            
            video_formats.sort(key=lambda x: (
                -int(x['resolution'].split('x')[1]) if 'x' in x.get('resolution', '') else 0,
                -x.get('tbr', 0)
            ), reverse=True)
            
            audio_formats.sort(key=lambda x: -x.get('tbr', 0))
            
            sorted_formats = video_formats + audio_formats
            
            return render_template_string(FORMATS_PAGE, url=url, formats=sorted_formats)

    except Exception as e:
        import traceback
        print("❌ get_formats error:")
        traceback.print_exc()
        return render_template_string(HOME_PAGE, error=f"Fetch error: {str(e)}")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    video_format = request.form.get("video_format")
    audio_format = request.form.get("audio_format")
    
    if not url or not video_format or not audio_format:
        return render_template_string(HOME_PAGE, error="Missing URL or format selection")

    try:
        file_id = str(uuid.uuid4())
        video_path = f"/tmp/{file_id}_video.mp4"
        audio_path = f"/tmp/{file_id}_audio.m4a"
        output_path = f"/tmp/{file_id}.mp4"
        
        print(f"📥 Starting download for: {url}")
        print(f"📹 Video format: {video_format}")
        print(f"🎵 Audio format: {audio_format}")

        # Download video
        ydl_opts_video = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'format': video_format,
            'outtmpl': video_path,
            'quiet': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            print("⏬ Downloading video...")
            ydl.download([url])

        # Download audio
        ydl_opts_audio = {
            'cookiefile': COOKIES_FILE if cookies_content else None,
            'format': audio_format,
            'outtmpl': audio_path,
            'quiet': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            print("⏬ Downloading audio...")
            ydl.download([url])

        # Merge with ffmpeg
        print("🎬 Merging with ffmpeg...")
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ FFmpeg failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return render_template_string(HOME_PAGE, error=f"Merge failed: {result.stderr}")

        print(f"✅ Merged video saved to {output_path}")

        # Cleanup
        os.remove(video_path)
        os.remove(audio_path)
        print("🧹 Temp files removed")

        download_url = f"/download-file/{file_id}.mp4"
        return render_template_string(HOME_PAGE, video_url=download_url)

    except Exception as e:
        print("💥 Server error:")
        import traceback
        traceback.print_exc()
        return render_template_string(HOME_PAGE, error=f"Server error: {str(e)}")

@app.route("/download-file/<filename>")
def download_file(filename):
    file_path = f"/tmp/{filename}"
    if not os.path.exists(file_path):
        return "File not found", 404

    def cleanup():
        time.sleep(30)
        try:
            os.remove(file_path)
            print(f"🗑️ Cleaned up {file_path}")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    threading.Thread(target=cleanup, daemon=True).start()

    response = send_file(
        file_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name=filename
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
