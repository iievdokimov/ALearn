import traceback
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_word_data_webster(word):
    # data = {}
    # data_Thes = get_data_Thes(word, api_key_Thes)
    WEBSTER_DICT_API_KEY = os.getenv('WEBSTER_DICT_API_KEY')
    WEBSTER_THESUARUS_API_KEY = os.getenv('WEBSTER_THESAURUS_API_KEY')

    data_Dict = get_data_Dict(word, WEBSTER_DICT_API_KEY)
    data = data_Dict

    return data


def parse_definition_list(definition : list) -> str:
    if isinstance(definition, str):
        return definition
    elif isinstance(definition, list) and len(definition) > 0:
        return parse_definition_list(definition[0])
    else:
        return ""


def get_data_Thes(word, api_key):
    '''
    :param word:
    :return: DATA FEATURES AVAILABLE IN THIS REFERENCE
        Synonyms
        Related words
        Near antonyms
        Antonyms
        Idiomatic phrases
        Concise definitions
        Examples
        Spelling suggestions
    '''
    api_key_Thesaurus = api_key
    url = (f"https://www.dictionaryapi.com/api/v3/references/thesaurus/json/"
                f"{word}?"
                f"key={api_key_Thesaurus}")

    resp = requests.get(url=url)
    data = resp.json()
    return data


def find_vis_entries(data):
    vis_entries = []
    res = []

    def recursive_search(d):
        if isinstance(d, dict):
            for key, value in d.items():
                print("rec KV", key, value)
                if isinstance(value, list):
                    if 'vis' == value[0]:
                        vis_entries.extend(value)
                        res.extend(value)
                    else:
                        for el in value:
                            recursive_search(el)
                elif isinstance(value, dict):
                    recursive_search(value)
        elif isinstance(d, list):
            if len(d) > 0:
                if d[0] == 'vis':
                    res.extend(d)
                    return
            for item in d:
                recursive_search(item)

    recursive_search(data)
    return res


def get_data_Dict(word, api_key):
    '''
    :param word:
    :return: DATA FEATURES AVAILABLE IN THIS REFERENCE
        Definitions
        Examples
        Etymologies
        Synonym and Usage paragraphs
        Pronunciation symbols
        Audio pronunciations
        Illustrations
        Spelling suggestions
    '''

    api_key_Dict = api_key
    url = (f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/"
           f"{word}?"
           f"key={api_key_Dict}")

    try:
        resp = requests.get(url=url)
        data = resp.json()
    except:
        return {}

    res_data = []
    for i in range(len(data)):
        data_part = {
            "word_id": "",
            "definition": "",
            "part_of_speech": "",
            "examples": [],
            "etymology": "",
            "synonyms": "",
            "usage_paragraphs": [],
            "pronunciation_symbols": "",
            "audio": "",
            "illustrations": "",
            "spelling_suggestions": ""
        }
        try:
            data_part["examples"] = find_vis_entries(data[i])
        except:
            traceback.print_exc()
            pass
        try:
            data_part["word_id"] = data[i]['meta']['id']
        except:
            traceback.print_exc()
            pass
        try:
            data_part["definition"] = parse_definition_list(data[i]["shortdef"])
        except:
            traceback.print_exc()
            pass
        try:
            data_part["part_of_speech"] = data[i]['fl']
        except:
            traceback.print_exc()
            pass
        res_data.append(data_part)

    return res_data


# word = input()
# print(get_data_Dict(word))
#
# # while True:
# #     word = input()
# #     print(get_word_data_webster(word))
