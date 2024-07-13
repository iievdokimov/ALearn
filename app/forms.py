from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField,
                     SubmitField, FieldList, SelectField)
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User

from flask import flash


def word_exists(word):
    # flash(f"if word exitsts: {word}")
    if word == "1" or word == "2":
        return False
    return True


class NewWordsGroup(FlaskForm):
    words = FieldList(StringField('word'), min_entries=2, max_entries=15)
    submit = SubmitField('Create')

    def validate_word(self, word):
        # flash("Validating new word")
        if not word_exists(word):
            raise ValidationError('No such word. Please check the spelling.')


class DefinitionSelectionForm(FlaskForm):
    word = StringField('Word', render_kw={'readonly': True})
    # definitions = FieldList(StringField('Definition'))
    definitions = SelectField('Definitions', choices=[], coerce=int, validators=[DataRequired()])
    # selected_definition = StringField('Selected Definition', validators=[DataRequired()])
    submit = SubmitField('Create Group')

# class DefinitionSelectionForm(FlaskForm):
#     word = HiddenField('Word')
#     definitions = SelectField('Definitions', choices=[])
#     submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')