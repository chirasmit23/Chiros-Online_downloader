from flask import Flask, render_template, request, jsonify,send_file
import os
import uuid
import time
import redis
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import yt_dlp

# Load environment variables
load_dotenv()

# Upstash Redis Setup
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        password=REDIS_PASSWORD,
        ssl=True,
        decode_responses=True
    )
except Exception as e:
    print(f"Redis Connection Error: {e}")
    redis_client = None  # Continue without Redis if it fails

# Instagram Credentials
USERNAME = os.getenv("INSTA_USERNAME")
PASSWORD = os.getenv("INSTA_PASSWORD")

# Validate credentials
if not USERNAME or not PASSWORD:
    raise ValueError("Instagram username or password not set in .env file")

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# Set downloads folder
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# Rate Limiting Function
def is_rate_limited(ip, limit=10, duration=60):
    if redis_client:
        key = f"rate_limit:{ip}"
        try:
            with redis_client.pipeline() as pipe:
                pipe.incr(key)
                pipe.expire(key, duration)
                count = int(pipe.execute()[0])
                return count > limit
        except Exception as e:
            print(f"Redis Error: {e}")
    return False  # If Redis fails, allow access

# Function to Log in and Download Instagram Post
def download_instagram_post(post_url,username,password):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))).click()
        time.sleep(5)
        
        driver.get(post_url)
        time.sleep(5)
        media_element = driver.find_element(By.XPATH, "//video | //img")
        media_url = media_element.get_attribute("src")
        driver.quit()
        
        filename = f"instagram_post_{uuid.uuid4().hex}.mp4" if "video" in media_url else f"instagram_post_{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(DOWNLOADS_FOLDER, filename)
        response = requests.get(media_url, stream=True)
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filepath
    except Exception as e:
        print(f"Instagram Download Error: {e}")
        return None
    finally:
        driver.quit()

# Function to Download Videos with Quality Selection
def download_video(url, quality):
    unique_filename = f"downloaded_video_{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(DOWNLOADS_FOLDER, unique_filename)

    quality_formats = {
        "1080": "bestvideo[height<=1080]+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best",
        "480": "bestvideo[height<=480]+bestaudio/best",
        "best": "bestvideo+bestaudio/best"
    }
    video_format = quality_formats.get(quality, "bestvideo+bestaudio/best")

    ydl_opts = {
        "format": video_format,
        "outtmpl": video_path,
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(video_path):
            return video_path
    except Exception as e:
        print(f"Download Error: {e}")
    
    return None

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video", methods=["GET", "POST"])
def video_downloader():
    if request.method == "GET":
        return render_template("index.html")

    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    url = request.form.get("url")
    quality = request.form.get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filepath = download_video(url, quality)  # This function should return a valid file path

    if filepath and os.path.exists(filepath):
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="video/mp4"
        )
    else:
        return jsonify({"error": "Could not download the video"}), 500
@app.route("/instagram", methods=["GET", "POST"])
def photo_downloader():
    if request.method == "GET":
        return render_template("instagram_downloader.html")
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    
    post_url = request.form.get("url")
    if not post_url:
        return jsonify({"error": "No URL provided"}), 400
    
    filepath = download_instagram_post(post_url,"username","password")
    mimetype = "video/mp4" if filepath.endswith(".mp4") else "image/jpeg"
    if filepath and os.path.exists(filepath):
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype=mimetype
        )
    else:
        return jsonify({"error": "Could not download the image"}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port, debug=True)
