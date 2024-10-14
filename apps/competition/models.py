from datetime import datetime
from enum import Enum as PyEnum

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

from apps import db, login_manager
from apps.authentication.util import hash_pass
from kaggle_utils import HTML, get_competition_picture

# db.Model = declarative_base()

# Association table for user competition records
user_competition = Table(
    "user_competition",
    db.Model.metadata,
    Column("user_id", ForeignKey("Users.id"), primary_key=True),
    Column("competition_id", ForeignKey("competitions.id"), primary_key=True),
    Column("best_score", db.Float, nullable=True),
    Column("notebook_link", db.String(1024), nullable=True),
    Column(
        "last_updated_time", DateTime, default=datetime.now(), onupdate=datetime.now()
    ),
)


class Users(db.Model, UserMixin):
    __tablename__ = "Users"

    id = Column(db.Integer, primary_key=True)
    username = Column(db.String(64), unique=False)
    email = Column(db.String(64), unique=True)
    image = Column(
        db.Text, nullable=True, default="/static/assets/img/theme/team-4.jpg"
    )
    password = Column(db.LargeBinary)
    rating = Column(db.Integer, default=0)
    is_admin = Column(db.Boolean, default=False)
    user_name_in_kaggle = Column(db.String(64), nullable=True)

    competitions = relationship(
        "Competitions", secondary=user_competition, back_populates="users"
    )

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]
            if property == "password":
                value = hash_pass(value)
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = Users.query.filter_by(username=username).first()
    return user if user else None


class OAuth(OAuthConsumerMixin, db.Model):
    __tablename__ = "oauth"

    user_id = Column(db.Integer, ForeignKey(Users.id))
    user = relationship(Users)


class DifficultyEnum(PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Competitions(db.Model):
    __tablename__ = "competitions"

    id = Column(db.Integer, primary_key=True)
    name = Column(db.Text, nullable=False, unique=True)
    image = Column(db.Text)
    is_authenticated = Column(db.Boolean)
    difficulty = Column(Enum(DifficultyEnum), nullable=False)
    resources = Column(db.JSON, nullable=True)
    notes = Column(db.Text, nullable=True)
    template_urls = Column(db.JSON, nullable=True)

    users = relationship(
        "Users", secondary=user_competition, back_populates="competitions"
    )

    def __init__(
        self,
        name,
        difficulty,
        is_authenticated,
        resources=None,
        notes=None,
        template_urls=None,
    ):
        html = HTML(name)
        if not html.is_competition_page():
            raise ValueError("Invalid URL")

        self.name = name
        self.image = get_competition_picture(name)
        self.difficulty = difficulty
        self.resources = resources if resources is not None else []
        self.notes = notes
        self.template_urls = template_urls if template_urls is not None else []

    def get_achievers_count(self):
        return len(self.users)
