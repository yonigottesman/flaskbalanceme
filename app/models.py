from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    transactions = db.relationship('Transaction', backref='owner',
                                   lazy='dynamic',
                                   cascade='all, delete, delete-orphan')
    categories = db.relationship('Category', backref='owner',
                                 lazy='dynamic',
                                 cascade='all, delete, delete-orphan')
    subcategories = db.relationship('Subcategory', backref='owner',
                                    lazy='dynamic',
                                    cascade='all, delete, delete-orphan')
    rules = db.relationship('Rule', backref='owner',
                            lazy='dynamic',
                            cascade='all, delete, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, index=True)
    merchant = db.Column(db.String(64), index=True)
    amount = db.Column(db.Float)
    comment = db.Column(db.String(128), index=True)
    source = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'))

    def valueOf(tdict, user):
        return Transaction(date=tdict['date'],
                           merchant=tdict['merchant'],
                           amount=tdict['amount'],
                           comment=tdict['comment'],
                           source=tdict['source'],
                           owner=user,
                           subcategory=tdict['subcategory'])

    def to_dict(self):
        return {'date': self.date,
                'merchant': self.merchant,
                'amount': self.amount,
                'comment': self.comment,
                'source': self.source,
                'tx_id': self.id,
                'subcategory': self.subcategory.name}

    def update(self, tdict):
        # self.date = dt.strptime(tdict['date'], '%Y-%m-%d')
        self.merchant = tdict['merchant']
        self.amount = tdict['amount']
        self.comment = tdict['comment']
        self.source = tdict['source']
        self.subcategory = tdict['subcategory']

    def column(name):
        string_to_column = {'date': Transaction.date,
                            'merchant': Transaction.merchant,
                            'amount': Transaction.amount,
                            'comment': Transaction.comment,
                            'source': Transaction.source,
                            'subcategory': Transaction.subcategory_id}
        return string_to_column[name]
    
    def __str__(self):
        return str(self.to_dict())

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subcategories = db.relationship('Subcategory', backref='category',
                                    lazy='dynamic', cascade='delete')


class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    transactions = db.relationship('Transaction', backref='subcategory',
                                   lazy='dynamic', cascade='delete')
    rules = db.relationship('Rule', backref='subcategory',
                            lazy='dynamic', cascade='delete')


class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64), index=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
