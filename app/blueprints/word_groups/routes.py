from flask import (render_template, flash,
                   redirect, url_for, request, jsonify)

from app.forms import (DefinitionSelectionForm)
from flask_login import (current_user)
from wtforms.validators import ValidationError

from app import db
from app.forms import (NewWordsGroup)
from flask_login import (login_required)
import sqlalchemy as sa
from app.models import WordGroup, Definition, Word
from typing import cast

from app.blueprints.word_groups.definitions import get_definitions_for_word

from . import word_groups_bp


@word_groups_bp.route('/group_formation', methods=['GET', 'POST'])
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
        return redirect(url_for('word_groups.select_definitions', words=words))

    return render_template('group_formation.html', form=form)


def create_word_group(user_id, selected_definitions):
    new_group = WordGroup(user_id=user_id)
    for item in selected_definitions:
        definition = db.session.scalars(sa.select(Definition).where(
            cast("ColumnElement[bool]", Definition.id == item['definition_id']))).first()

        if definition:
            new_group.words_definitions.append(definition)
    db.session.add(new_group)
    db.session.commit()


@word_groups_bp.route('/mpf/<int:group_id>', methods=['GET', 'POST'])
@login_required
def get_group_MPF(group_id):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.id == group_id)).order_by(sa.desc(WordGroup.created_at))
    group = db.session.scalars(query).first()

    words = []
    for definition in group.words_definitions:
        words.append(form_MPF_data(definition))

    return render_template('group_MPF.html', words=words)


def form_MPF_data(definition):
    res = {}
    res["word"] = definition.word_text
    res["definition"] = definition.text
    res["part_of_speech"] = definition.part_of_speech
    res["examples"] = definition.examples
    return res

@word_groups_bp.route('/learn_group', methods=['GET', 'POST'])
@login_required
def learn_group():
    # TODO
    # if user got group learn
    # else redirect for create new group
    return redirect(url_for('main.index'))


@word_groups_bp.route('/see_group_results', methods=['GET', 'POST'])
@login_required
def see_group_results():
    # TODO
    # return render_template('group_formation.html')
    return redirect(url_for('main.index'))

@word_groups_bp.route('/select_definitions', methods=['GET', 'POST'])
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
        return redirect(url_for('main.user', username=current_user.username))

    return render_template('select_definitions.html', forms=forms)


@word_groups_bp.route('/validate_word', methods=['POST'])
def validate_word():
    word = request.json['word']
    form = NewWordsGroup()
    try:
        form.validate_word(word)
        return jsonify({'is_valid': True})
    except ValidationError as e:
        return jsonify({'is_valid': False, 'error': str(e)})


@word_groups_bp.route('/see_all_words', methods=['GET', 'POST'])
@login_required
def see_all_words():
    # TODO
    # debug function: removal's possible
    query = sa.select(Word)
    words = db.session.scalars(query).all()
    return render_template('see_all_words.html', words=words)


@word_groups_bp.route('/acquaint_words_meaning/<int:group_id>')
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
        return redirect(url_for('main.index'), )
    return render_template('acquaint_words_meaning.html', word_group=word_group)
