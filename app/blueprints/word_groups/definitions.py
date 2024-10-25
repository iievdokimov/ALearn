from .word_tools import WebsterDictionary
from typing import cast


from app.extensions import db
from app.models import Word, Definition, sa

def get_definitions_for_word(word_text):
    words_data = WebsterDictionary.get_word_data_webster(word_text)

    # check if word in dictionary
    if not WebsterDictionary.in_Webster(words_data):
        word_text = words_data[0]
        words_data = None

    word = db.session.scalars(sa.select(Word).where(
        cast("ColumnElement[bool]", Word.word_text == word_text))).first()
    if not word:
        word = Word(word_text=word_text)
        db.session.add(word)
        db.session.commit()

    if word.definitions:
        return word.definitions
    add_definitions_to_db(word, word_text, words_data)

    return word.definitions


def add_definitions_to_db(word, word_text, words_data):
    if not words_data:
        words_data = WebsterDictionary.get_word_data_webster(word_text)

    # flash(f"WebsterAPI data: {words_data}")
    for data in words_data:
        definition_text = data["definition"]
        word_text = data["word_id"]
        part_of_speech = data["part_of_speech"]
        examples = "in dev"
        new_definition = Definition(text=definition_text, part_of_speech=part_of_speech,
                                    examples=examples, word=word, word_text=word_text)
        word.definitions.append(new_definition)
        db.session.add(new_definition)
    db.session.commit()