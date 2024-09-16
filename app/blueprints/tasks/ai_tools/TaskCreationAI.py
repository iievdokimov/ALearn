import os
from dotenv import load_dotenv
# from openai import OpenAI
# import openai
import httpx
import json
import re
from app.blueprints.tasks.task_tools.FillGapTask.GapSentence import GapSentence
from app.blueprints.tasks.task_tools.CCQTask.CCQSentence import CCQSentence

load_dotenv()


PROXY_API_KEY = os.getenv('PROXY_API_KEY')

if not PROXY_API_KEY:
    raise ValueError("PROXY_API_KEY key not found. Please set the OPENAI_API_KEY environment variable.")
else:
    print(f"PROXY_API_KEY key loaded: {PROXY_API_KEY[:5]}...")


def perform_request_with_proxy(prompt):
    # not to ask costy api by accident
    return {}
    proxyapi_url = 'https://api.proxyapi.ru/openai/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {PROXY_API_KEY}',
        'Content-Type': 'application/json'
    }

    json_data = {
        #'model': 'gpt-4o',  # Используйте подходящую модель
        'model': 'gpt-3.5-turbo-0125',
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        'max_tokens': 100,
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
        print("MyResp:", response)
        return response



# def get_ai_answer(promt):
#     ans = perform_request_with_proxy(promt).json()
#     print("ans", ans)
#     ans = ans['choices']
#     print("ans_choices", ans)
#     ans = ans[0]
#     print("ans_choices[0]", ans)
#     ans = ans['message']
#     print("ans[choices][0][message]", ans)
#     ans = ans['content']
#     print("ans[choices][0][message][content]", ans)
#     ans = json.loads(ans)
#     print("json", ans)
#     return ans

def get_ai_answer(prompt):
    try:
        # Выполняем запрос и получаем ответ
        ans = perform_request_with_proxy(prompt).json()

        # Пошаговая обработка ответа
        ans = ans['choices'][0]['message']['content']

        print("ans_content", ans)

        ans = clear_json_string(ans)
        print("content_cleared", ans)

        # Попытка преобразования в JSON
        try:
            ans_json = json.loads(ans)
            print("Valid JSON:", ans_json)
        except json.JSONDecodeError as e:
            print("Ошибка при преобразовании JSON:", str(e))
            return None

        return ans_json
    except (KeyError, IndexError) as e:
        print(f"Ошибка доступа к ключам или индексам: {str(e)}")
        return {}
    except:
        return {}



def clear_json_string(ans):
    ans = str(ans)
    # Удаляем лишние пробелы или символы, если они есть
    ans = ans.strip()
    ans = re.sub(r"^'''json\s*", '', ans)  # Удаляем '''json в начале строки
    ans = re.sub(r"\s*'''$", '', ans)  # Удаляем ''' в конце строки

    idx_start = 0
    idx_end = len(ans) - 1
    for i in range(len(ans)):
        if ans[i] == '{':
            idx_start = i
            break

    for i in range(len(ans) - 1, -1, -1):
        if ans[i] == '}':
            idx_end = i
            break

    ans = ans[idx_start:idx_end + 1]

    return ans



def parse_gap_answer(json_answer):
    return GapSentence(json_answer["start"], json_answer["end"], json_answer["answer"])


def parse_ccq_answer(json_answer):
    try:
        sentences = []
        for s in json_answer["sentences"]:
            sentences.append(CCQSentence(s[0], s[1]))
        return sentences
    except:
        return [CCQSentence("Error", "Yes")]


def generate_fill_the_gaps_task(words_with_definitions):
    task = {}
    for word_defined in words_with_definitions.word_defineds:
        word = word_defined.word.word_text
        definition = word_defined.definition.text
        promt = (f"Generate a sentence with the word '{word}' (in meaning: {definition}) "
                  f"and create a gap fill exercise. Provide the sentence in the format: "
                  f"'sentence with {word} as a gap'.")

        ai_answer = get_ai_answer(promt)
        generated_fill_obj = parse_gap_answer(ai_answer)
        task[word] = generated_fill_obj

    return task


def generate_ccqs_task(word_group):
    task = {}
    for definition in word_group.words_definitions:
        word = definition.word.word_text
        definition = definition.text
        # promt = (f'Сгенерируй три предложения про слово "{word}" в значении "{definition}".'
        #          f'Несколько из предложений должно быть ложными'
        #          f'(то есть это утверждение не верно для данного значения слова). '
        #          f'Верни ответ в формате JSON, где поле `sentences` содержит массив пар ["Предложение", "Yes" или "No"] '
        #          f'(где "Yes" означает правильное предложение, а "No" — ложное).'
        #          f'Учитывай, что эти предложения должны помогать с пониманием конкретного значения слова "{definition}" ')

        promt = (f'Сгенерируй три предложения про слово "{word}" в значении "{definition}". '
                 f'Одно или несколько из предложений должно быть ложным (то есть это утверждение не верно для данного значения слова). '
                 f'Верни ответ строго в формате JSON (JSON-строка), где поле `sentences` содержит массив пар ["Предложение", "Yes" или "No"]. '
                 f'Не добавляй никаких лишних символов или текста перед или после JSON-ответа'
                 f' - когда в поле content лежит строка начинающаяся с трех апострофов и слова json - твой респонс неверный. '
                 f'Учитывай, что эти предложения должны помогать с пониманием конкретного значения слова "{definition}".')

        ai_answer = get_ai_answer(promt)
        sentences = parse_ccq_answer(ai_answer)
        task[word] = sentences

    return task
