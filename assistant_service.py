import os
import json
from dotenv import load_dotenv
import openai

dotenv_path = os.path.join(os.getcwd(), "venv", "secrets.env")
load_dotenv(dotenv_path) 
openai.api_key = os.getenv("OPENAI_API_KEY")

# Reading the file of instructions
with open("instructions1.txt", "r", encoding="utf-8") as file:
    instructions = file.read()

# Define the files' paths
knowledge_base_file_path = "knowledge_base.pdf"
products_file_path = "new_products.xlsx"
assistant_file_path = "assistant.json"

# Create the Assistant if it does not exist
if not os.path.exists(assistant_file_path):
    knowledge_file = openai.files.create(file=open(knowledge_base_file_path, "rb"), purpose="assistants")

    vector_store = openai.beta.vector_stores.create(
        name="Technology store consultant vector store",
        file_ids=[knowledge_file.id]
    )

    products_file = openai.files.create(file=open(products_file_path, "rb"), purpose="assistants")

    assistant = openai.beta.assistants.create(
        name="MPK Technology Assistant",
        instructions=instructions,
        tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
        tool_resources={
            "file_search": {"vector_store_ids": [vector_store.id]},
            "code_interpreter": {"file_ids": [products_file.id]}
        },
        model="gpt-4o"
    )

    with open(assistant_file_path, "w", encoding="utf-8") as f:
        json.dump(assistant.model_dump(), f, indent=4) 

else:
    with open(assistant_file_path, "r", encoding="utf-8") as f:
        assistant = json.load(f)


