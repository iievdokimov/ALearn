from flask import (render_template, flash,
                   redirect, url_for, request, jsonify,
                   session)

from app.extensions import db
from app.forms import (LoginForm, RegistrationForm)
from flask_login import (current_user, login_user,
                         logout_user, login_required)
import sqlalchemy as sa
from urllib.parse import urlsplit
from app.models import User, Word, WordGroup, Definition
from typing import cast


from . import main_bp


@main_bp.route('/',  methods=['GET', 'POST'])
@main_bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title='Home')


@main_bp.route('/user/<username>')
@login_required
def user(username):
    query = sa.select(WordGroup).where(
        cast("ColumnElement[bool]", WordGroup.user_id == current_user.id)).order_by(sa.desc(WordGroup.created_at))
    word_groups = db.session.scalars(query).all()
    return render_template('user.html', word_groups=word_groups)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))