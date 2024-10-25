from flask import (render_template, flash,
                   redirect, url_for, request, session)

from app import db
from app.forms import (MatchDefinitionsForm, FillGapForm,
                       CCQForm)
from flask_login import (current_user, login_required)
import sqlalchemy as sa
from app.models import Word, WordGroup
from typing import cast
import random


from . import tasks_bp


@tasks_bp.route('/task_fill_the_gaps/<int:group_id>', methods=['GET', 'POST'])
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

    task_data = []
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


@tasks_bp.route('/check_task_fill_gaps/<int:group_id>')
@login_required
def check_task_fill_gaps(group_id):
    # TODO
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


@tasks_bp.route('/task_match_definitions/<int:group_id>', methods=['GET', 'POST'])
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


@tasks_bp.route('/check_task_match_definitions/<int:group_id>', methods=['GET', 'POST'])
@login_required
def check_task_match_definitions(group_id):
    # TODO
    # 1. counting result
    # 2. saving group result for user

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


@tasks_bp.route('/task_ccqs/<int:group_id>', methods=['GET', 'POST'])
@login_required
def task_ccqs(group_id):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.id == group_id)).order_by(sa.desc(WordGroup.created_at))
    group = db.session.scalars(query).first()

    if not group:
        return render_template('404.html')

    # USE MOCK
    # not to pay for API
    task = [
        {"definition": "some def 1", "word": "some word 1",
         "sentences": [("I am dumb.", "Yes"), ("Notu dummy me are.", "No")]
         },
        {"definition": "very fishy", "word": "fish",
         "sentences": [("Fish Kills.", "Yes"), ("Kill fish.", "No")]
         }
    ]

    # USE MOCK
    # not to pay for API
    #
    # task = []
    # ai_task = TaskCreationAI.generate_ccqs_task(group)
    # for word in ai_task.keys():
    #     word_ccq = {}
    #     word_ccq["word"] = word
    #     word_ccq["sentences"] = []
    #     for ccq_sentence in ai_task[word]:
    #         word_ccq["sentences"].append(ccq_sentence.lightFormat())
    #     task.append(word_ccq)

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


@tasks_bp.route('/check_task_ccqs/<int:group_id>', methods=['GET', 'POST'])
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
