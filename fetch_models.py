import requests
import json

def get_free_models():
    response = requests.get("https://openrouter.ai/api/v1/models")
    if response.status_code == 200:
        models = response.json().get('data', [])
        free_models = [m['id'] for m in models if 'free' in m['id']]
        print(json.dumps(free_models, indent=2))
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    get_free_models()
