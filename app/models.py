from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import String, Integer, Table, Column, ForeignKey, DateTime
from app import app, db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from sqlalchemy.orm import relationship


words_groups_association = Table(
    'groups_association',
    db.Model.metadata,
    Column('definition_id', Integer, ForeignKey('definition.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('word_group.id'), primary_key=True)
)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    word_groups = relationship('WordGroup',
                               back_populates='user', order_by='desc(WordGroup.created_at)')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_text = db.Column(db.String(80), unique=True, nullable=False)
    definitions = relationship('Definition', back_populates='word')

    def __repr__(self):
        return f'<Word {self.word_text}>'


class Definition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_text = db.Column(db.String(64))
    text = db.Column(db.Text, nullable=False)
    part_of_speech = db.Column(db.String(20))
    examples = db.Column(db.Text)
    word_id = db.Column(db.Integer, ForeignKey('word.id'), nullable=False)
    word = relationship('Word', back_populates='definitions')

    groups = relationship('WordGroup', secondary=words_groups_association, back_populates='words_definitions')

    def __repr__(self):
        return f"{self.word_text} ({self.part_of_speech}) - {self.text}"


class WordGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='word_groups')
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    words_definitions = relationship('Definition', secondary='groups_association', back_populates='groups')

    # info fields
    # group progress
    # common mistakes



# class WordDefined(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     word_id = db.Column(db.Integer, ForeignKey('word.id'), nullable=False)
#     definition_id = db.Column(db.Integer, ForeignKey('definition.id'), nullable=False)
#     word = relationship('Word')
#     definition = relationship('Definition')
#     word_groups = relationship('WordGroup', secondary=wordgroup_worddefined, back_populates='word_defineds')
#     __table_args__ = (db.UniqueConstraint('word_id', 'definition_id', name='_word_definition_uc'),)


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Word': Word, 'WordGroup': WordGroup}
