from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import LoginForm, RegistrationForm, NewWordsGroup
from flask_login import current_user, login_user, logout_user
from flask_login import login_required
import sqlalchemy as sa
from app import db
from app.models import User
from flask import request
from urllib.parse import urlsplit
from app.models import User, Word, WordGroup
from flask import request, jsonify
from app.forms import NewWordsGroup
from wtforms.validators import ValidationError


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
        new_group = WordGroup(user_id=current_user.id)
        for word_data in form.words:
            if word_data.data == "":
                continue
            # flash(f"{word_data.data}\n")
            # TODO
            # CHECK if word in DB already
            word = db.session.scalars(sa.select(Word).where(Word.word_text == word_data.data)).first()
            if not word:
                word = Word(word_text=word_data.data, meaning=word_data.data)


            db.session.add(word)
            db.session.commit()
            new_group.words.append(word)

        db.session.add(new_group)
        db.session.commit()
        flash('You,ve created group!')
        return redirect(url_for(f'acquaint_words_meaning', group_id=new_group.id))

    return render_template('group_formation.html', form=form)


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
        return redirect(url_for('index'))
    return render_template('acquaint_words_meaning.html', word_group=word_group)

# @app.route('/acquaint_word_meaning/<word>')
# @login_required
# def acquaint_word_meaning(word):
#     pass


@app.route('/user/<username>')
@login_required
def user(username):
    # user = current_user
    query = sa.select(WordGroup).where(WordGroup.user_id == current_user.id).order_by(sa.desc(WordGroup.created_at))
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