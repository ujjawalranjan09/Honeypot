import google.generativeai as genai
from config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    print("No GEMINI_API_KEY found in config")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    with open("models_list.txt", "w") as f:
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
        except Exception as e:
            f.write(f"Error listing models: {e}\n")
