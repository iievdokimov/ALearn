import os
from dotenv import load_dotenv
# from openai import OpenAI
# import openai
import httpx

load_dotenv()

# client = OpenAI()


# Получение API ключа OpenAI
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# openai.api_key = OPENAI_API_KEY

PROXY_API_KEY = os.getenv('PROXY_API_KEY')

if not PROXY_API_KEY:
    raise ValueError("PROXY_API_KEY key not found. Please set the OPENAI_API_KEY environment variable.")
else:
    print(f"PROXY_API_KEY key loaded: {PROXY_API_KEY[:5]}...")


def perform_request_with_proxy(prompt):
    proxyapi_url = 'https://api.proxyapi.ru/openai/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {PROXY_API_KEY}',
        'Content-Type': 'application/json'
    }

    json_data = {
        'model': 'gpt-4o',  # Используйте подходящую модель
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        'max_tokens': 50,
        'n': 1,
        'stop': None,
        'temperature': 0.7,
    }

    with httpx.Client(http2=True) as client:
        response = client.post(
            proxyapi_url,
            headers=headers,
            json=json_data
        )
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response



def generate_fill_the_gaps_task(words_with_definitions):
    task = {}
    for word_defined in words_with_definitions.word_defineds:
        word = word_defined.word.word_text
        definition = word_defined.definition.text
        prompt = (f"Generate a sentence with the word '{word}' (in meaning: {definition}) "
                  f"and create a gap fill exercise. Provide the sentence in the format: "
                  f"'sentence with {word} as a gap'.")

        # Попытка выполнения запроса с несколькими прокси
        try_count = 5
        response = None
        for _ in range(try_count):
            try:
                response = perform_request_with_proxy(prompt)
                if response.status_code == 200:
                    break
            except httpx.ProxyError as e:
                print(f"Proxy error: {e}. Retrying with a new proxy...")

        if response and response.status_code == 200:
            response_json = response.json()
            if 'choices' in response_json and response_json['choices']:
                sentence_with_gap = response_json['choices'][0]['message']['content'].strip()
                task[word] = sentence_with_gap
            else:
                print(f"Unexpected response structure: {response_json}")
        else:
            print(
                f"Request failed after {try_count} attempts with status code {response.status_code if response else 'N/A'}: {response.text if response else 'No response'}")

    return task

