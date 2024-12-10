from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from uuid import uuid4

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(20), primary_key=True, default=str(uuid4()))
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    @classmethod
    def get_user_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_user_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def create_user(cls, username, password):
        return cls(username=username, password=generate_password_hash(password, "scrypt", 50))

    def __repr__(self):
        return super().__repr__()
