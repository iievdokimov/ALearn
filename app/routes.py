from flask import (render_template, flash,
                   redirect, url_for, request, jsonify)
from app import app
from app import db
from app.forms import (LoginForm, RegistrationForm,
                       NewWordsGroup, DefinitionSelectionForm)
from flask_login import (current_user, login_user,
                         logout_user, login_required)
import sqlalchemy as sa
from urllib.parse import urlsplit
from app.models import User, Word, WordGroup, WordDefined, Definition
from wtforms.validators import ValidationError
from wtforms import StringField
from app.word_tools import WebsterDictionary
from typing import cast


@app.route('/',  methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    query = sa.select(Word)
    words = db.session.scalars(query).all()
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
            word = db.session.scalars(sa.select(Word).where(Word.word_text == word_data.data)).first()
            if not word:
                word = Word(word_text=word_data.data)
                db.session.add(word)
                db.session.commit()
            words.append(word_data.data)
        return redirect(url_for(f'select_definitions', words=words))

    return render_template('group_formation.html', form=form)


def get_definitions_for_word(word_text):
    word = db.session.scalars(sa.select(Word).where(
        cast("ColumnElement[bool]", Word.word_text == word_text))).first()
    if not word:
        return []

    if word.definitions:
        return word.definitions

    add_definitions_to_db(word, word_text)

    return word.definitions


def add_definitions_to_db(word, word_text):
    words_data = WebsterDictionary.get_word_data_webster(word_text)
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
    #TODO
    # revision

    # flash("Creating group:")
    # flash(selected_definitions)
    #
    # words = db.session.scalars(sa.select(Word)).all()
    # flash("words=")
    # for word in words:
    #     flash(word)
    #
    # flash(selected_definitions[0]["definition_id"])

    # defs = db.session.scalars(sa.select(Definition).where(
    #     cast('ColumnElement[bool]', Definition.id == selected_definitions[0]["definition_id"])
    # )).all()
    # flash("defs=")
    # for el in defs:
    #     flash(el.id)
    #     flash(el.word_text)
    new_group = WordGroup(user_id=user_id)
    for item in selected_definitions:
        word = db.session.scalars(sa.select(Word).where(
            cast("ColumnElement[bool]", Word.word_text == item['word']))).first()
        definition = db.session.scalars(sa.select(Definition).where(
            cast("ColumnElement[bool]", Definition.id == item['definition_id']))).first()
        word_defined = WordDefined(word_id=word.id, definition_id=definition.id)
        new_group.word_defineds.append(word_defined)
    db.session.add(new_group)
    db.session.commit()


@app.route('/select_definitions', methods=['GET', 'POST'])
@login_required
def select_definitions():
    words = request.args.getlist('words')
    forms = []

    for word in words:
        definitions = get_definitions_for_word(word)
        form = DefinitionSelectionForm()
        form.word.data = word
        # form.definitions.entries = [StringField(default=definition) for definition in definitions]
        form.definitions.choices = [(definition.id, definition.__repr__()) for definition in definitions]
        forms.append(form)

    if request.method == 'POST':
        selected_definitions = []
        for form in forms:
            selected_definitions.append({
                'word': form.word.data,
                'definition_id': form.definitions.data
            })
        # Сохраняем группу слов с выбранными определениями
        create_word_group(current_user.id, selected_definitions)
        # flash("SUCCESS")
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
    # user = current_user
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