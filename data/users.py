import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    basket = orm.relation("Basket", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Basket(SqlAlchemyBase):
    __tablename__ = 'basket'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    product_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("products.id"))
    count = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    user = orm.relation('Users')


class Products(SqlAlchemyBase):
    __tablename__ = 'products'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    name_of_photo = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    categories = orm.relation("Category",
                              secondary="products_to_category",
                              backref="products")


products_to_category = sqlalchemy.Table('products_to_category', SqlAlchemyBase.metadata,
    sqlalchemy.Column('product', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('products.id')),
    sqlalchemy.Column('category', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('category.id'))
)


class Category(SqlAlchemyBase):
    __tablename__ = 'category'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)


class Reviews(SqlAlchemyBase):
    __tablename__ = 'reviews'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    review = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    mark = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    product_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("products.id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("users.id"))
