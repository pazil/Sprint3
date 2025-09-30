from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.responses.create(
  model="gpt-5-nano",
  input=[
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "[SYSTEM PROMPT WILL GO HERE]"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "[INPUT TEXT WILL GO HERE]"
        }
      ]
    }
  ],
  text={
    "format": {
      "type": "json_object"
    },
    "verbosity": "medium"
  },
  reasoning={
    "effort": "medium",
    "summary": "auto"
  },
  tools=[],
  store=False,
  include=[
    "reasoning.encrypted_content",
    "web_search_call.action.sources"
  ]
)