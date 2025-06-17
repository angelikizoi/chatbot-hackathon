import openai
import os
from dotenv import load_dotenv

# Load API key and organization from environment variables
load_dotenv("secrets.env")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

client = openai.OpenAI(
    api_key=openai.api_key,
    organization=openai.organization
)

client.files.create(
  file=open("dataset.jsonl", "rb"),
  purpose="fine-tune"
)
#
#After creating the file
response = client.files.list()
print(response.data)

client.fine_tuning.jobs.create(
  training_file="file-nWtA5eTo133GwYIutD0CVbo3",
  model="gpt-3.5-turbo-0125"
)

#List 10 fine-tuning jobs
# finetune_job = client.fine_tuning.jobs.list(limit=5)
# print(finetune_job.data)

initial_prompt = """
    You are a case interview preparation assistant who plays the role of an interviewer at a top level
    management consulting firm. You are going to conduct a case interview which will consists of a prompt
    about a business problem, 1 approach structuring question, 1 qualitative question, 1 quantitative question,
    and a request for a recommendation. After the prompt about a business problem the candidate can ask
    clarifying questions about the case, but he doesn't have to, after which he is expected to come up with
     an approach to the problem. As part of the quantitative question ask the candidate to calculate something
     related to the business problem. After the candidate provides a recommendation during the last part
     of the case you need to strictly evaluate how a candidate performed, explain why you evaluated him like
     that and suggest areas of improvement. Don't share with the candidate that you are going to evaluate his
     performance. Overall you should judge the candidate on how well he came up with a structured approach
     to the problem and how structured he was when he answered the questions, how well he performed mathematical
      calculations, how well he was able to drive the case forward by suggesting next steps, what was the
      breath of his ideas when answering qualitative questions, how well he showed his business sense.
    """

message = [{'role': 'system', 'content': initial_prompt}]


completion = client.chat.completions.create(
  model="ft:gpt-3.5-turbo-0125:personal::99Vw4GZW",
  messages = message,
  max_tokens= 200,
)
print(completion.choices[0].message)