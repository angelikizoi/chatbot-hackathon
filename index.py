from flask import Flask, request, jsonify, render_template
import mysql.connector
import openai
import os
from dotenv import load_dotenv
import base64
import time
import queue
import json
import sounddevice as sd
# from vosk import Model, KaldiRecognizer
from assistant_service import upload_image
from utilities_service import remove_image, download_image

app = Flask(__name__)

# Path to store the recorded audio files
UPLOAD_FOLDER = os.path.abspath("uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# OpenAI API Key
dotenv_path = os.path.join(os.getcwd(), "venv", "secrets.env")
load_dotenv(dotenv_path)
openai.api_key = os.getenv("OPENAI_API_KEY")

# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

# # Load Vosk for real-time STT
# vosk_model_path = "D:\\vosk-model-en-us-0.22"
# vosk_model = Model(vosk_model_path)
# audio_q = queue.Queue()

# def audio_callback(indata, frames, time, status):
#     """Vosk Callback function to store real-time audio data"""
#     if status:
#         print(status, flush=True)
#     audio_q.put(bytes(indata))

# def real_time_stt():
#     """Perform real-time STT if speech duration is short"""
#     recognizer = KaldiRecognizer(vosk_model, 16000)
#     with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
#                            channels=1, callback=audio_callback):
#         print("🎤 Listening for short speech...")
#         start_time = time.time()

#         while True:
#             data = audio_q.get()
#             if recognizer.AcceptWaveform(data):
#                 result = json.loads(recognizer.Result())
#                 speech_duration = time.time() - start_time

#                 # Switch to full recording if speech is too long
#                 if speech_duration > 10:  # Threshold: 5 seconds
#                     print("⚠️ Long speech detected! Switching to full recording mode...")
#                     return None  # Indicate long speech mode

#                 print("You said:", result["text"])
#                 return result["text"]

def record_audio(file_name, duration=10):
    """Record full speech if the user speaks for long"""
    import wave
    import pyaudio

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    frames = []

    print("🎙️ Recording full audio...")
    for _ in range(0, int(16000 / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(file_name, 'wb')
    
    try:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    finally:
        wf.close()  # Ensure the file is properly closed

def convert_audio_to_text_whisper(audio_file):
    """Transcribe long speech using Whisper API"""
    with open(audio_file, "rb") as file:
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            file=file,
            language="en"
        )
    print(transcription.text)
    return transcription.text


def extract_text_response(ai_response):
    """Extracts text and JSON product data from mixed AI responses."""

    if isinstance(ai_response, dict):  # If AI already returns structured JSON
        return ai_response.get("text_response", "").strip(), ai_response.get("products", [])

    if isinstance(ai_response, str):  # If response is a string, process it
        # ✅ DEBUG: Print AI response before extraction
        print(f"🔍 RAW AI Response:\n{ai_response}\n")

        # ✅ Improved regex (handles missing "json")
        import re
        pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
        match = pattern.search(ai_response)

        json_part = None
        text_part = ai_response.strip()  # Default to full response if no JSON is found

        if match:
            json_part = match.group(1).strip()  # Extract JSON block
            text_part = pattern.sub("", ai_response).strip()  # Remove JSON from response
            print(f"✅ JSON Extracted:\n{json_part}\n")
            print(f"✅ Remaining Text:\n{text_part}\n")
        else:
            print("❌ No JSON found in AI response!")

        # Try parsing JSON if found
        product_data = []
        text_data = ''
        if json_part:
            try:
                product_data = json.loads(json_part).get("products", [])
                text_data = json.loads(json_part).get("text_response", "").strip()
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parsing Error: {e}")

        return text_data if text_data else text_part, product_data

    return None, []  # Default case if AI response is invalid


def convert_text_to_speech(text):
    """Convert AI response to speech"""
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    return response.content  # Returns the audio binary

def fetch_products(query):
    """Fetch product details from the database based on AI-generated query."""
    print(f"Executing SQL Query: {query}")
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Ensure only SELECT queries are executed
        if not query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Invalid SQL query: Only SELECT statements are allowed."}) 

        cursor.execute(query)
        products = cursor.fetchall()

        if not products:
            return json.dumps({"error": "No matching products found."})  

        return json.dumps(products)

    except mysql.connector.Error as e:
        return json.dumps({"error": str(e)})

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route("/", methods=["GET"])
def home():
    return render_template('index.html')

# # Create a new chat
@app.route("/start", methods=["GET"])
def start_chat():
    thread = openai.beta.threads.create()
    return jsonify({"thread_id": thread.id})

@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        print("❌ No audio file received.")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    file_path = os.path.join(UPLOAD_FOLDER, "input_audio.wav")

    try:
        audio_file.save(file_path)
        print(f"✅ Audio file saved at: {file_path}")
        return jsonify({"file_path": file_path, "audio_url": f"/uploads/input_audio.wav"})
    except Exception as e:
        print(f"❌ Failed to save audio file: {e}")
        return jsonify({"error": "Failed to save audio file"}), 500

# Send and Receive a message
@app.route("/chat", methods=["POST"])
def chat():
    try:
        from assistant_service import assistant
        assistant_id = assistant["id"]
        data = request.get_json()

        # **1️⃣ Ensure thread_id is present**
        thread_id = data.get("thread_id")
        if not thread_id:
            print("🔄 Creating new thread...")
            thread_response = openai.beta.threads.create()
            thread_id = thread_response.id

        # **2️⃣ Handle Message Input (Text & Audio)**
        message = data.get("message", {})  # Get message if text is sent
        if 'audio' in message:
            file_path = message["audio"]
        else:
            file_path = False

        print(f"📩 Received data: Audio File: {file_path}, Message: {message}")

        new_message = {"role": "user", "content": []}  # AI message structure
        transcribed_text = None

        # **3️⃣ Process Audio File If Sent**
        if file_path:
            absolute_file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_path))  # Convert to absolute path
            print(f"🔊 Processing audio file: {absolute_file_path}")

            # Check if file exists before processing
            if not os.path.exists(absolute_file_path):
                print(f"❌ ERROR: File not found - {absolute_file_path}")
                return jsonify({"error": "Audio file not found"}), 400

            # **Transcribe Audio**
            transcribed_text = convert_audio_to_text_whisper(absolute_file_path)
            print(f"📝 Transcription: {transcribed_text}")

            # **Delete the audio file after transcription**
            try:
                os.remove(absolute_file_path)
                print(f"🗑️ Deleted file: {absolute_file_path}")
            except Exception as e:
                print(f"⚠️ Could not delete file: {absolute_file_path}, Error: {e}")

            # **Include transcription in AI message**
            new_message["content"].append({"type": "text", "text": f"📝 Transcription: {transcribed_text}"})

        # **4️⃣ Process Text Input If Sent**
        if "text" in message:
            new_message["content"].append({"type": "text", "text": message["text"]})

        # **Ensure we have a message to send**
        if not new_message["content"]:
            print("❌ No valid input (text or audio) received.")
            return jsonify({"error": "No valid message content provided"}), 400

        # **5️⃣ Send Message to AI Assistant**
        openai.beta.threads.messages.create(
            thread_id=thread_id, role=new_message["role"], content=new_message["content"]
        )

        print("=RUN=")
        run = openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

        while run.status in ["queued", "in_progress"]:
            time.sleep(5)
            run = openai.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            
        print(run.status)
        if run.status != "completed":
            error_message = getattr(run, "error", {}).get("message", "Unknown error")
            print(f"❌ Assistant run failed: {error_message}")
            return jsonify({"response": "Sorry. I'm having a problem answering this. Please ask something different."})

        print("=Get Messages=")
        messages = openai.beta.threads.messages.list(run.thread_id)
        response_text = messages.data[0].content[0].text.value
        print(f"🤖 AI Response: {response_text}")

        # **6️⃣ Extract Text & Product Data**
        text_response, product_data = extract_text_response(response_text)

        # **7️⃣ Convert AI Response to Speech**
        speech_response = convert_text_to_speech(text_response)
        speech_base64 = base64.b64encode(speech_response).decode('utf-8')

        # **8️⃣ Return AI Response & Transcription**
        return jsonify({
            "text_response": text_response,
            "transcription": transcribed_text,  # Now chatbot will display this
            "products": product_data if product_data else [],
            "speech_response": speech_base64
        })

    except Exception as e:
        print("❌ Error in /chat:", e)
        return jsonify({"response": "Sorry. I'm having a problem answering this. Please ask something different."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
