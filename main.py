from flask import Flask, send_file, Response
import os
import requests
import threading
import subprocess
import time
from datetime import datetime

app = Flask(__name__)
LOG_FILE_PATH = 'recoadings.txt'  # Adjust for your directory
BOT_TOKEN = '7049818211:AAHpIjXLIkM5wHYOSuazfz0KlVFB-nHMXMA'
CHAT_ID = '1137065263'  # Replace with your chat ID or group ID
PLAYERX_API_KEY = '46topBnuEaqZ5FRf'  # Use your PlayerX API key
PLAYERX_API_URL = 'https://playerx.api/upload'  # Adjust if necessary
STREAM_URL = 'http://103.84.57.155:8000/play/a03t/index.m3u8'  # Replace with the actual stream URL

# Function to send message to Telegram bot
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

# Route to show logs in terminal-like format
@app.route('/')
def show_logs():
    def generate():
        with open(LOG_FILE_PATH, 'r') as log_file:
            while True:
                line = log_file.readline()
                if not line:
                    break
                yield line + '<br/>'  # Format for web display
    return Response(generate(), mimetype='text/html')

# Route to download the recoadings.txt file
@app.route('/recoading.txt')
def download_logs():
    return send_file(LOG_FILE_PATH, as_attachment=True)

# Function to send recoadings.txt to Telegram
@app.route('/record')
def send_recordings():
    files = {'document': open(LOG_FILE_PATH, 'rb')}
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument?chat_id={CHAT_ID}'
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        return "recoadings.txt sent to Telegram successfully!"
    else:
        return "Failed to send recoadings.txt."

# Function to upload to PlayerX
def upload_to_playerx(file_path, timing):
    files = {'files[]': open(file_path, 'rb')}
    data = {
        'api_key': PLAYERX_API_KEY,
        'action': 'upload_video',
        'raw': 0
    }
    try:
        response = requests.post(PLAYERX_API_URL, files=files, data=data)
        response_json = response.json()

        # Log results to recoadings.txt
        with open(LOG_FILE_PATH, 'a') as log_file:
            if response_json.get('status') == 'success':
                video_url = response_json.get('slug')
                log_file.write(f"{datetime.now()} - Success: {video_url}\n")
                print(f"Video uploaded successfully: {video_url}")
            else:
                log_file.write(f"{datetime.now()} - Error: Unable to upload file for timing {timing}. Response: {response_json}\n")
                print(f"Error during upload for timing {timing}")
    except Exception as e:
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(f"{datetime.now()} - Error: Exception occurred for timing {timing}. Details: {str(e)}\n")
        print(f"Exception during upload: {str(e)}")

# Function to record and upload in 30-minute intervals
def record_and_upload():
    while True:
        start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"output_{start_time}.mp4"
        
        # FFmpeg command to record for 30 minutes (1800 seconds)
        ffmpeg_command = [
            'ffmpeg', '-i', STREAM_URL,
            '-t', '1800', '-c:v', 'copy', '-c:a', 'copy',
            output_file
        ]

        # Start recording
        print(f"Recording started: {start_time}")
        subprocess.run(ffmpeg_command)

        # Upload the recorded file to PlayerX
        timing_info = f"{start_time} - 30-minute chunk"
        upload_to_playerx(output_file, timing_info)

        # Remove the file after upload to save storage
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Deleted local file: {output_file}")

        # Optional short sleep to handle edge cases
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=record_and_upload).start()
    app.run(debug=True)
                
