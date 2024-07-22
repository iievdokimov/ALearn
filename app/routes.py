from flask import (render_template, flash,
                   redirect, url_for, request, jsonify,
                   session)

from app import app
from app import db
from app.forms import (LoginForm, RegistrationForm,
                       NewWordsGroup, DefinitionSelectionForm, MatchDefinitionsForm, FillGapForm,
                       CCQForm)
from flask_login import (current_user, login_user,
                         logout_user, login_required)
import sqlalchemy as sa
from urllib.parse import urlsplit
from app.models import User, Word, WordGroup, Definition
from wtforms.validators import ValidationError
from app.word_tools import WebsterDictionary
from app.task_tools import TaskCreationAI
from typing import cast
import random


@app.route('/',  methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title='Home')


@app.route('/group_formation', methods=['GET', 'POST'])
@login_required
def group_formation():
    form = NewWordsGroup()
    if form.validate_on_submit():
        words = []
        for word_data in form.words:
            if word_data.data == "":
                continue
            words.append(word_data.data)

        # session['words'] = words
        return redirect(url_for(f'select_definitions', words=words))

    return render_template('group_formation.html', form=form)


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


def create_word_group(user_id, selected_definitions):
    new_group = WordGroup(user_id=user_id)
    for item in selected_definitions:
        definition = db.session.scalars(sa.select(Definition).where(
            cast("ColumnElement[bool]", Definition.id == item['definition_id']))).first()

        if definition:
            new_group.words_definitions.append(definition)
    db.session.add(new_group)
    db.session.commit()


@app.route('/select_definitions', methods=['GET', 'POST'])
@login_required
def select_definitions():
    words = request.args.getlist('words')
    # words = session.get('words', [])
    forms = []

    # flash("in select")
    i = 0
    for word in words:
        definitions = get_definitions_for_word(word)
        # flash(word)
        # flash(definitions)
        single_form = DefinitionSelectionForm(prefix=f"word_{i}")
        single_form.word.data = word
        single_form.definitions.choices = [(definition.id, definition.__repr__()) for definition in definitions]
        forms.append(single_form)
        i += 1

    selected_definitions = []
    if request.method == 'POST':
        # all_valid = True
        for form in forms:
            selected_definitions.append({
                'word': form.word.data,
                'definition_id': form.definitions.data
            })

        # flash(selected_definitions)
        create_word_group(current_user.id, selected_definitions)
        flash("success: saving group")
        return redirect(url_for('user', username=current_user.username))

    return render_template('select_definitions.html', forms=forms)


@app.route('/validate_word', methods=['POST'])
def validate_word():
    word = request.json['word']
    form = NewWordsGroup()
    try:
        form.validate_word(word)
        return jsonify({'is_valid': True})
    except ValidationError as e:
        return jsonify({'is_valid': False, 'error': str(e)})


@app.route('/learn_group', methods=['GET', 'POST'])
@login_required
def learn_group():
    # TODO
    # if user got group learn
    # else redirect for create new group
    return render_template('index.html')


@app.route('/see_group_results', methods=['GET', 'POST'])
@login_required
def see_group_results():
    # TODO
    return render_template('group_formation.html')


@app.route('/see_all_words', methods=['GET', 'POST'])
@login_required
def see_all_words():
    # TODO
    # debug function: removal's possible
    query = sa.select(Word)
    words = db.session.scalars(query).all()
    return render_template('see_all_words.html', words=words)


@app.route('/acquaint_words_meaning/<int:group_id>')
@login_required
def acquaint_words_meaning(group_id):
    query = sa.select(WordGroup).where(WordGroup.id == group_id).order_by(sa.desc(WordGroup.created_at))
    word_group = db.session.scalars(query).first()
    if not word_group:
        #TODO
        # err logics
        pass
    # check if group_id in user's groups
    if word_group.user_id != current_user.id:
        return redirect(url_for('index'), )
    return render_template('acquaint_words_meaning.html', word_group=word_group)


# @app.route('/acquaint_word_meaning/<word>')
# @login_required
# def acquaint_word_meaning(word):
#     pass


@app.route('/user/<username>')
@login_required
def user(username):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.user_id == current_user.id)).order_by(sa.desc(WordGroup.created_at))
    word_groups = db.session.scalars(query).all()
    return render_template('user.html', word_groups=word_groups)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/task_fill_the_gaps/<int:group_id>', methods=['GET', 'POST'])
@login_required
def task_fill_the_gaps(group_id):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.id == group_id))
    words_with_definitions = db.session.scalars(query).first()

    # if not words_with_definitions:
    #     return render_template('404.html')


    task = [{"sentence_start": "i live", "sentence_end": "life", "answer": "ddd"},
            {"sentence_start": "i fuck", "sentence_end": "somebody", "answer": "dda"}]
    answers = {}
    for el in task:
        answers[el["sentence_start"] + el["sentence_end"]] = el["answer"]

    forms = []
    i = 0
    for sentence in task:
        form = FillGapForm(prefix=f"gap_{i}")
        form.sentence_start.data = sentence["sentence_start"]
        form.sentence_end.data = sentence["sentence_end"]
        forms.append(form)
        i += 1

    task_data  = []
    if request.method == 'POST':
        for form in forms:
            task_data.append({
                'sentence_start': form.sentence_start.data,
                'sentence_end': form.sentence_end.data,
                'user_word': form.answer.data,
                'answer_word': answers[form.sentence_start.data + form.sentence_end.data]
            })

        session['task_data'] = task_data
        return redirect(url_for('check_task_fill_gaps', group_id=group_id,
                                task_data=task_data))

    # task = TaskCreationAI.generate_fill_the_gaps_task(words_with_definitions)
    return render_template('task_fill_in_the_gaps.html', task=task, forms=forms,
                           group_id=group_id)

    
@app.route('/check_task_fill_gaps/<int:group_id>')
@login_required
def check_task_fill_gaps(group_id):
    #TODO
    # 1. counting result
    # 2. saving group result for user

    task_data = session.get('task_data', [])
    flash(task_data)

    points = 0
    all_points = 0
    if isinstance(task_data, list) and len(task_data) > 0:
        for result in task_data:
            if result['user_word'] == result['answer_word']:
                points += 1
            all_points += 1

        query = sa.select(WordGroup).where(
            cast("ColumnElement[bool]", WordGroup.id == group_id))
        group = db.session.scalars(query).first()
        group.points_ratio_fill_gaps = points / all_points
        db.session.commit()

    return render_template('check_task_fill_gaps.html', task_data=task_data,
                           points=points, all_points=all_points)


def create_task_match_definitions(group):
    task = {"words": [], "definitions": []}
    answers = {}
    for definition in group.words_definitions:
        task["words"].append(definition.word_text)
        task["definitions"].append(definition.text)
        answers[definition.text] = definition.word_text

    random.shuffle(task["words"])
    random.shuffle(task["definitions"])

    return task, answers


@app.route('/task_match_definitions/<int:group_id>', methods=['GET', 'POST'])
@login_required
def task_match_definitions(group_id):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.id == group_id)).order_by(sa.desc(WordGroup.created_at))
    group = db.session.scalars(query).first()

    if not group:
        return render_template('404.html')

    task, answers = create_task_match_definitions(group)

    forms = []
    i = 0
    for definition in task["definitions"]:
        form = MatchDefinitionsForm(prefix=f"def_{i}")
        form.definition.data = definition
        forms.append(form)
        i += 1

    # user_answers = []
    task_data = []
    if request.method == 'POST':
        # all_valid = True
        for form in forms:
            task_data.append({
                'definition': form.definition.data,
                'user_word': form.answer.data,
                'answer_word': answers[form.definition.data]
            })

        # flash(task_data)
        # flash("success: saving user_answers")
        # task_data_json = json.dumps(task_data)
        session['task_data'] = task_data
        # task_data = {"user": user_answers, "correct": answers}
        return redirect(url_for('check_task_match_definitions', group_id=group_id,
                                task_data=task_data))

    return render_template('task_match_definitions.html', forms=forms,
                           words=task['words'], group_id=group_id)


@app.route('/check_task_match_definitions/<int:group_id>', methods=['GET', 'POST'])
@login_required
def check_task_match_definitions(group_id):
    #TODO
    # 1. counting result
    # 2. saving group result for user

    # task_data_json = request.args.get('task_data_json')
    # task_data = []
    # if task_data_json:
    #     task_data = json.loads(task_data_json)

    task_data = session.get('task_data', [])

    points = 0
    all_points = 0
    if isinstance(task_data, list) and len(task_data) > 0:
        for result in task_data:
            if result['user_word'] == result['answer_word']:
                points += 1
            all_points += 1

        query = sa.select(WordGroup).where(
            cast("ColumnElement[bool]", WordGroup.id == group_id))
        group = db.session.scalars(query).first()
        group.points_ratio_math_definitions = points / all_points
        db.session.commit()

    # flash(f"GET TASK: {task_data}")
    return render_template('check_task_match_definitions.html', task_data=task_data,
                           points=points, all_points=all_points)


@app.route('/task_ccqs/<int:group_id>', methods=['GET', 'POST'])
@login_required
def task_ccqs(group_id):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.id == group_id)).order_by(sa.desc(WordGroup.created_at))
    group = db.session.scalars(query).first()

    if not group:
        return render_template('404.html')

    task = [
        {"definition": "some def 1", "word": "some word 1",
         "sentences": [("I am dumb.", "Yes"), ("Notu dummy me are.", "No")]
         },
        {"definition": "very fishy", "word": "fish",
         "sentences": [("Fish Kills.", "Yes"), ("Kill fish.", "No")]
         }
    ]

    answers = {}

    grouped_forms = []
    i = 0
    for word_item in task:
        forms = []
        for sentence in word_item["sentences"]:
            form = CCQForm(prefix=f"ccq_{i}")
            form.sentence.data = sentence[0]
            answers[sentence[0]] = sentence[1]
            forms.append(form)
            i += 1
        data = {"word": word_item["word"], "forms": forms}
        grouped_forms.append(data)

    task_data = []
    if request.method == 'POST':
        forms = []
        for el in grouped_forms:
            forms += el["forms"]

        for form in forms:
            task_data.append({
                'sentence': form.sentence.data,
                'user_word': form.answer.data,
                'answer_word': answers[form.sentence.data]
            })

        flash(task_data)
        session['task_data'] = task_data
        return redirect(url_for('check_task_ccqs', group_id=group_id,
                                task_data=task_data))

    return render_template('task_ccqs.html', grouped_forms=grouped_forms)


@app.route('/check_task_ccqs/<int:group_id>', methods=['GET', 'POST'])
@login_required
def check_task_ccqs(group_id):
    task_data = session.get('task_data', [])

    points = 0
    all_points = 0
    if isinstance(task_data, list) and len(task_data) > 0:
        for result in task_data:
            if result['user_word'] == result['answer_word']:
                points += 1
            all_points += 1

        # query = sa.select(WordGroup).where(
        #     cast("ColumnElement[bool]", WordGroup.id == group_id))
        # group = db.session.scalars(query).first()
        # group.points_ratio_ccqs = points / all_points
        # db.session.commit()

    return render_template('check_task_ccqs.html', task_data=task_data,
                           points=points, all_points=all_points)

