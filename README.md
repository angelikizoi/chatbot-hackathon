# MPK Technology Chatbot Assistant

## Overview

This project was developed as part of the **Hackathon 2025**, organized by **Athens University of Economics and Business (AUEB)**. It was built in response to a challenge set by a company looking to explore smart assistant technologies in e-commerce. Within just **one week**, our team designed and implemented a fully functional AI chatbot tailored for a technology-focused e-commerce platform.

The chatbot serves as a **smart virtual assistant** for an online store selling a range of high-tech products such as **laptops, monitors, smartwatches, smartphones, tablets, headphones, printers**, and **storage devices**.

## Purpose

The goal was to build a **proof-of-concept assistant** that demonstrates:

* Natural and interactive customer communication
* Intelligent product recommendations
* Enhanced accessibility through **voice-based input and output**

## Main Functionalities

* **Text-to-Text:** Customer types a message, and the chatbot replies with intelligent product recommendations or answers.
* **Speech-to-Text:** Users can send audio input which is transcribed and processed by the assistant.
* **Text-to-Speech:** AI-generated replies can be played back as audio, enhancing accessibility and realism.

## Project Structure and Key Components

### `index.py`

This is the main **Flask application**, which handles:

* Serving the front-end interface
* Handling HTTP endpoints (`/chat`, `/start`, `/upload-audio`)
* Integrating OpenAI's GPT and Whisper APIs
* Managing file uploads, audio processing, and assistant conversations

### `assistant_service.py`

Handles initialization and configuration of the **OpenAI Assistant**, including:

* Loading API keys
* Creating vector stores and assistants if not already saved
* Linking knowledge documents and tools like `code_interpreter`

### `utilities_service.py`

Contains helper functions for:

* Downloading images
* Cleaning up temporary files after processing

### `index.html`

A clean and user-friendly **chat interface** with support for sending messages, recording audio, and displaying product recommendations as cards.

### `new_products.xlsx`

A mock product database representing the company's inventory. It includes structured data such as:

* Product Name
* Category
* Description
* Price
* Image URL

This file simulates the output of a real database query and is used by the assistant’s `code_interpreter` to recommend matching products.

### `instructions1.txt`

This file contains detailed **instructions and behavioral logic** for the assistant. It guides how the assistant should:

* Greet and engage customers
* Interpret needs and preferences
* Respond with valid product matches
* Return responses in structured JSON

### `knowledge_base.pdf`

A summarized **knowledge base** describing company policies, products, shipping methods, warranties, and FAQs. This file enhances the assistant’s understanding of business rules and improves its answers to customer queries.

## Technologies Used

* **Python 3**
* **Flask** for web server and API
* **OpenAI API** (GPT-4o, Whisper, TTS)
* **HTML/CSS/JavaScript** for the front-end
* **MySQL (optional)** for structured queries
* **PyAudio** and **SoundDevice** for voice recording

## Setup

1. Clone the repo
2. Create a virtual environment and activate it
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the Flask app:

```bash
python index.py
```

5. Visit `http://localhost:8080` to start chatting!

## Notes

* This is a demo version for hackathon purposes. It uses static files (like Excel and PDF) to simulate real-world systems.
* No real product inventory or payment systems are connected.

## Acknowledgments

Special thanks to **AUEB** and the hosting company for this opportunity. This project reflects what a dedicated team can achieve in a short time with modern AI tools.

---

Built with ❤️ during Hackathon 2025
