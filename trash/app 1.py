from flask import Flask, request, jsonify
import mysql.connector
import openai
import os
from dotenv import load_dotenv
from flask_cors import CORS
import re
from pydub import AudioSegment
import base64
import wave

# Load environment variables
load_dotenv("secrets.env")

# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = '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'
client = openai.OpenAI(api_key=openai.api_key)


# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
#

def extract_keywords(user_message):

    prompt = (
        "Your task is to extract keywords from the given user query. "
        "Only return a single keyword if it matches exactly one of the following categories: "
        "Smartphone, Laptop, Monitor, Tablet, Smartwatch, Hard drives, Printer, or Headphones. "
        "Do not add extra words, synonyms, or explanations. "
        "If the user mentions multiple categories, return them as a comma-separated list. "
        "Additionally, detect price-related queries like 'cheapest' and similar or 'under $500' and similar and return them as well. "
        "If none of these categories are mentioned, return an empty string."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]
    )
    keywords = response.choices[0].message.content.strip()
    return keywords if keywords else None  # Return None if empty

# Function to fetch products
def fetch_products(keywords):
    print(keywords)
    if not keywords:
        return []
    conn = None
    cursor = None
    products = ""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        keyword_list = [k.strip() for k in keywords.split(",")] if "," in keywords else [keywords]
        price_query = None
        for keyword in keyword_list:
            if "cheapest" in keyword.lower():
                price_query = "cheapest"
            elif "under" in keyword.lower():
                match = re.search(r'(\d+)', keyword)  # Extract numerical value (price)
                if match:
                    price_query = int(match.group(1))
        if price_query == "cheapest":
            query = "SELECT * FROM product WHERE category IN ({}) ORDER BY price ASC LIMIT 1".format(
                ", ".join(["%s"] * len(keyword_list))
            )
            cursor.execute(query, keyword_list)
        elif isinstance(price_query, int):
            placeholders = ", ".join(["%s"] * len(keyword_list))  # Correctly format placeholders
            query = f"SELECT * FROM product WHERE category IN ({placeholders}) AND price <= %s"
            cursor.execute(query, keyword_list + [price_query])
        else:
            query = "SELECT * FROM product WHERE category IN ({})".format(
                ", ".join(["%s"] * len(keyword_list))
            )
            cursor.execute(query, keyword_list)
        products = cursor.fetchall()
        print (products)
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

    return products

conversation_history = []
def generate_response(user_message):
    keywords = extract_keywords(user_message)
    products = fetch_products(keywords)

    if len(conversation_history) > 20:
        conversation_history.pop(0)

    # Add user's message to history
    conversation_history.append({"role": "user", "content": user_message})

    product_list = "\n".join([f"- {p['name']} ({p['price']}€): {p['description']}" for p in products])

    final_prompt = (
        "You are a helpful shopping assistant having a conversation with a user. "
        "Based on the list of available products, respond in a friendly and engaging way. "
        "If the list is empty, apologize and say we don't currently have these items. "
        "If the user asked for the cheapest product, highlight the most affordable option found. "
        "If they asked for products under a specific price, list only the available options. "
        "Do not ask additional questions.\n\n"
        f"Product List:\n{product_list}"
    )
    conversation_history.append({"role": "system", "content": final_prompt})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages =
            # {"role": "user", "content": user_message},
            # {"role": "system", "content": final_prompt},
            conversation_history + [{"role": "user", "content": str(products)}],
            max_tokens=120
    )
    ai_response = response.choices[0].message.content
    # Store AI response in conversation history
    conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response

# Convert WAV to MP3
# def convert_wav_to_mp3(input_file, output_file):
#     sound = AudioSegment.from_wav(input_file)
#     sound.export(output_file, format="mp3")
#
# # Placeholder functions for Whisper, GPT-4, and TTS
# def convert_audio_to_text(audio_file):
#     """
#     Converting audio to text using Whisper
#     :param audio_file: format .mp3
#     :return: String (text)
#     """
#     audio_file = open(audio_file, "rb")
#     transcription = client.audio.transcriptions.create(
#         model="whisper-1",
#         file=audio_file,
#         language="en"
#     )
#     print(transcription.text)
#     return str(transcription.text)

# Chatbot Route
@app.route('/chat', methods=['POST'])
def chatbot():

    data = request.get_json()
    user_message = data.get("message", "")
    print(user_message)
    response = generate_response(user_message)

    return jsonify({"reply": response})

# # Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

