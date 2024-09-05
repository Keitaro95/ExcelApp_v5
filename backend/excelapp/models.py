# OAuthを使ってgoogleで認証する
from excelapp import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin

import string, random, datetime

class PrintInfo:
    def __init__(self, papersize, orientation, fitToWidth, fitToHeight):
        self.papersize = papersize
        self.orientation = orientation
        self.fitToWidth = fitToWidth
        self.fitToHeight = fitToHeight

@login_manager.user_loader #ユーザがログインしてたら働く関数
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True, unique=True, nullable=False)
    username = db.Column(db.String(64))
    password = db.Column(db.String(128))
    #紐付けに使うのは両者にない固有の変数でok
    filedatas = db.relationship('Asset', backref='user', lazy=True)
    # これだとfiladataはまだないから参照不可能
    # filedata = db.relationship('Filedata', backref="users", lazy='dynamic')
    
    def __init__(self, email, username=None, password=None):
        self.email = email
        self.username = username
        if password is None:
            letters = string.ascii_lowercase
            password = ''.join(random.choice(letters) for _ in range(10))
        self.password = generate_password_hash(password)

    @classmethod
    def select_by_id(cls, id):
        return cls.query.filter(cls.id==id).first()

    @classmethod
    def select_by_email(cls, email):
        return cls.query.filter(cls.email==email).first()

    def add_user(self):
        db.session.add(self)
        db.session.commit()
    
    def delete_user(self):
        db.session.delete(self)
        db.session.commit()


class Asset(db.Model):
    __tablename__ = 'assets'
    file_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_name  = db.Column(db.String, unique=True, nullable=False)
    asset_path = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploadtime = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, asset_name, asset_path, user_id):
        # file_idはautoなので書かなくてよし
        self.asset_name = asset_name
        self.asset_path = asset_path
        self.user_id = user_id

    def add_asset(self):
        db.session.add(self)
        db.session.commit()

    def delete_asset(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def asset_by_userid(cls, user_id):
        return cls.query.filter(cls.user_id==user_id).first()

    @classmethod
    def asset_by_fileid(cls, file_id):
        return cls.query.filter(cls.file_id==file_id).first()

    # file_idかつuser_idで一意に選択
    @classmethod
    def get_one_asset(cls, file_id, user_id):
        return cls.query.filter(cls.file_id==file_id, cls.user_id==user_id).first()