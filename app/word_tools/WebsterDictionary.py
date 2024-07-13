import traceback
import requests


def get_word_data_webster(word):
    # data = {}
    # data_Thes = get_data_Thes(word)
    data_Dict = get_data_Dict(word)
    data = data_Dict

    return data



def get_data_Thes(word):
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
    api_key_Thesaurus = ""
    url = (f"https://www.dictionaryapi.com/api/v3/references/thesaurus/json/"
                f"{word}?"
                f"key={api_key_Thesaurus}")

    resp = requests.get(url=url)
    data = resp.json()
    return data


def find_vis_entries(data):
    vis_entries = []
    res = []
    print()
    print("RECURSIVE-FIND")
    print()

    def recursive_search(d):
        if isinstance(d, dict):
            for key, value in d.items():
                print("rec KV", key, value)
                if isinstance(value, list):
                    print("LIST", value)
                    for el in value:
                        print(type(el), el)
                    print(value[0] == 'vis')
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
    # return vis_entries
    print("Found:", res)
    return res


def get_data_Dict(word):
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

    api_key_Dict = ""
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
            data_part["definition"] = data[i]["shortdef"]
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
