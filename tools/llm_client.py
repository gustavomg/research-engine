import os
import requests

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"
HF_URL = f"https://router.huggingface.co/v1/chat/completions"

def ask_llm(prompt, timeout=120):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.7
    }
    response = requests.post(HF_URL, headers=headers, json=payload, timeout=timeout)
    if response.status_code != 200:
        raise Exception(f"HF API error {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = ask_llm("Explain in 3 lines what a multi-agent system is.")
    print(result)
