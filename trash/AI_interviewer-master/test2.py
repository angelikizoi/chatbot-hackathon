from flask import Flask, request, jsonify

app = Flask(__name__)

# Define responses
responses = {
    "greetings": ["Hello!", "Hi there!", "Nice to meet you!"],
    "farewell": ["Goodbye!", "See you later!", "Have a great day!"],
}

icon = ("https://png.pngtree.com/png-clipart/20230401/original/"
        "pngtree-smart-chatbot-cartoon-clipart-png-image_9015126.png")

# Define function to get a response
def get_response(intent):
    if intent == "greet":
        return responses["greetings"]
    elif intent == "farewell":
        return responses["farewell"]
    else:
        return ["I'm sorry, I didn't understand that."]


# Define routes
@app.route("/")
def index():
    return "Hello, I am a chatbot!"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data["message"]

    # Placeholder logic to determine intent (you can replace this with your own logic)
    if "hello" in message.lower():
        intent = "greet"
    elif "bye" in message.lower():
        intent = "farewell"
    else:
        intent = "unknown"

    # Get response based on intent
    response = get_response(intent)

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)
