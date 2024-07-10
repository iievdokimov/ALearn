from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import String, Integer, Table, Column, ForeignKey
from app import app, db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash


words_in_process = db.Table('words_in_process',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    # db.Column('user_group_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('word_id', db.Integer, db.ForeignKey('word.id'), primary_key=True)
)


@login.user_loader
def load_user(id):
  return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    learning_words: so.Mapped[List['Word']] = so.relationship(
        'Word', secondary=words_in_process, lazy='dynamic',
        backref=db.backref('learners', lazy='dynamic')
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_text = db.Column(db.String(64), unique=True, nullable=False)
    meaning = db.Column(db.String(256))
    # другие поля для слова

    def __repr__(self):
        return f'<Word {self.word_text}>'


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Word': Word}
