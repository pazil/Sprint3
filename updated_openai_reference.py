from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file (override system env vars)
load_dotenv(override=True)

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "[SYSTEM PROMPT WILL GO HERE]"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "[INPUT TEXT WILL GO HERE]"
        }
      ]
    }
  ],
  response_format={
    "type": "json_object"
  },
  temperature=1,
  max_completion_tokens=4096,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)