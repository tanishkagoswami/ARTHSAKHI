import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit()

genai.configure(api_key=api_key)

print("Available Gemini models:\n")

for model in genai.list_models():
    print("Name:", model.name)
    print("Supported methods:", model.supported_generation_methods)
    print("-" * 50)