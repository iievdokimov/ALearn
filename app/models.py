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
    'words_groups',
    db.Model.metadata,
    Column('word_id', Integer, ForeignKey('word.id'), primary_key=True),
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
    word_text = db.Column(db.String(64), unique=True, nullable=False)
    meaning = db.Column(db.String(512))

    groups = relationship('WordGroup', secondary=words_groups_association, back_populates='words')

    def __repr__(self):
        return f'<Word {self.word_text}>'


class WordGroup(db.Model):
    id = Column(Integer, primary_key=True)
    # name = Column(String(100))
    user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.now(UTC))
    user = relationship('User', back_populates='word_groups')
    words = relationship('Word', secondary=words_groups_association,
                         back_populates='groups')

    # info fields
    # group progress
    # common mistakes


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Word': Word, 'WordGroup': WordGroup}
