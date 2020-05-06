from flask import Flask, render_template, redirect, abort, request
from data import db_session
from data.users import Users, Basket, Category, Products, Reviews
from data.db_session import global_init
from flask_login import LoginManager, logout_user, login_required, login_user, current_user
from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms import StringField, SubmitField, BooleanField, PasswordField, \
    FileField, TextAreaField
from wtforms.validators import DataRequired
import os
import random


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat password', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddProductForm(FlaskForm):
    name = StringField('Name of product', validators=[DataRequired()])
    name_of_photo = FileField('Name of photo of product that contains in /static/img',
                              validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    description = TextAreaField('Description of product', validators=[DataRequired()])
    categories = TextAreaField('Name of categories, if there is several add them between enter',
                               validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField('Submit')


class AddReview(FlaskForm):
    review_field = TextAreaField('Review', validators=[DataRequired()])
    mark = StringField('Mark: only number between 1 and 5', validators=[DataRequired()])
    submit = SubmitField('Submit')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(Users).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/", methods=['GET', 'POST'])
def index():
    global_init("db/shop.sqlite")
    session = db_session.create_session()
    products = session.query(Products).all()
    all_categories = session.query(Category).all()
    if request.method == 'POST':
        categories = request.form.getlist('category')
        search_string = request.form.getlist('search')[0]
        price_down = request.form.getlist('price_down')[0]
        price_up = request.form.getlist('price_up')[0]
        sort_by_price = request.form.getlist('price_sort')[0]
        sort_by_mark = request.form.getlist('mark_sort')[0]

        sorted_by_category = []
        for product in products:
            for category in categories:
                for product_category in product.categories:
                    if category.strip() == product_category.name.strip() and \
                            product not in sorted_by_category:
                        sorted_by_category.append(product)

        sorted_by_name = []
        if search_string.strip():
            for product in products:
                if search_string.strip().lower() in product.name.lower() or \
                        product.name.lower() in search_string.strip().lower():
                    sorted_by_name.append(product)

        if categories and search_string.strip() == '':
            products = sorted_by_category
        elif not categories and not search_string.strip() == '':
            products = sorted_by_name
        elif categories and not search_string.strip() == '':
            products = list(set(sorted_by_name) & set(sorted_by_category))

        if price_down.strip() and price_up.strip() and price_down.isdigit() and \
                price_up.isdigit():
            price_up, price_down = int(price_up), int(price_down)
            sorted_by_price = []
            for product in products:
                if price_down <= int(product.price) <= price_up:
                    sorted_by_price.append(product)
            products = list(set(products) & set(sorted_by_price))

        if sort_by_mark and sort_by_price:
            products_price_average_mark = []
            for product in products:
                reviews = session.query(Reviews).filter(Reviews.product_id == product.id).all()
                if not reviews:
                    average_now = 0
                    products_price_average_mark.append((product, product.price, average_now))
                    continue
                average_now = 0
                for review in reviews:
                    average_now += int(review.mark)
                average_now /= len(reviews)
                products_price_average_mark.append((product, product.price, average_now))
            if sort_by_mark == 'sort_by_mark' and sort_by_price == 'sort_by_price':
                sorted_products = sorted(products_price_average_mark,
                                         key=lambda x: (int(x[1]), -float(x[2])))
            elif sort_by_mark == 'sort_by_mark' and sort_by_price == 'sort_by_price_reverse':
                sorted_products = sorted(products_price_average_mark,
                                         key=lambda x: (-int(x[1]), -float(x[2])))
            elif sort_by_mark == 'sort_by_mark_reverse' and \
                    sort_by_price == 'sort_by_price_reverse':
                sorted_products = sorted(products_price_average_mark,
                                         key=lambda x: (-int(x[1]), float(x[2])))
            elif sort_by_mark == 'sort_by_mark_reverse' and sort_by_price == 'sort_by_price':
                sorted_products = sorted(products_price_average_mark,
                                         key=lambda x: (int(x[1]), float(x[2])))
            products = [product[0] for product in sorted_products]
        elif sort_by_mark and not sort_by_price:
            products_price_average_mark = []
            for product in products:
                reviews = session.query(Reviews).filter(Reviews.product_id == product.id).all()
                if not reviews:
                    average_now = 0
                    products_price_average_mark.append((product, average_now))
                    continue
                average_now = 0
                for review in reviews:
                    average_now += int(review.mark)
                average_now /= len(reviews)
                products_price_average_mark.append((product, average_now))
            if sort_by_mark == 'sort_by_mark':
                sorted_products = sorted(products_price_average_mark, key=lambda x: -float(x[1]))
            elif sort_by_mark == 'sort_by_mark_reverse':
                sorted_products = sorted(products_price_average_mark, key=lambda x: float(x[1]))
            products = [product[0] for product in sorted_products]
        elif not sort_by_mark and sort_by_price:
            if sort_by_price == 'sort_by_price':
                products = sorted(products, key=lambda x: int(x.price))
            elif sort_by_price == 'sort_by_price_reverse':
                products = sorted(products, key=lambda x: -int(x.price))

    average_mark = {}
    for product in products:
        reviews = session.query(Reviews).filter(Reviews.product_id == product.id).all()
        if not reviews:
            average_mark[product.id] = 'Without reviews'
            continue
        average_now = 0
        for review in reviews:
            average_now += int(review.mark)
        average_now /= len(reviews)
        average_mark[product.id] = average_now
    return render_template("index.html", products=products, all_categories=all_categories,
                           average_mark=average_mark)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        key = list('abcdefghijk')
        random.shuffle(key)
        key = ''.join(key)
        file_path = os.getcwd() + '/static/img/' + form.name.data + '_' + key + '.jpg'
        photo = request.files[form.name_of_photo.name]
        binary_f = photo.read()
        file = open(file_path, 'tw', encoding='utf-8')
        file.close()
        file = open(file_path, 'wb')
        file.write(binary_f)
        file.close()
        product = Products(
            name=form.name.data,
            name_of_photo=form.name.data + '_' + key + '.jpg',
            price=form.price.data,
            description=form.description.data
        )
        session.add(product)
        categories = form.categories.data.split('\n')
        for category_name in categories:
            found_category = session.query(Category).\
                filter(Category.name == category_name.strip()).first()
            if found_category:

                product.categories.append(found_category)

            else:
                new_category = Category(
                    name=category_name.strip()
                )
                session.add(new_category)
                session.commit()

                found_category = session.query(Category).\
                    filter(Category.name == category_name).first()
                product.categories.append(found_category)

        session.commit()
        return redirect("/")
    return render_template('add_product.html', title='Авторизация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(Users).filter(Users.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(Users).filter(Users.email == form.email.data).first():
            return render_template('register.html', title='Registration',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = Users(email=form.email.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Registration', form=form)


@app.route('/products_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    session = db_session.create_session()
    product = session.query(Products).filter(Products.id == id).\
        filter(current_user.id == 1).first()
    if product:
        session.delete(product)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/add_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    form = AddProductForm()
    if request.method == "GET":
        session = db_session.create_session()
        product = session.query(Products).filter(Products.id == id).\
            filter(current_user.id == 1).first()
        if product:
            form.name.data = product.name
            form.name_of_photo.data = product.name_of_photo
            form.price.data = product.price
            form.description.data = product.description
            to_categories = product.categories
            name_of_categories = []
            for to_category in to_categories:
                name_of_categories.append(to_category.name)
            form.categories.data = '\n'.join(name_of_categories)
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        product = session.query(Products).filter(Products.id == id).\
            filter(current_user.id == 1).first()
        if product:
            product.name = form.name.data

            key = list('abcdefghijk')
            random.shuffle(key)
            key = ''.join(key)
            file_path = os.getcwd() + '/static/img/' + form.name.data + '_' + key + '.jpg'
            photo = request.files[form.name_of_photo.name]
            binary_f = photo.read()
            file = open(file_path, 'tw', encoding='utf-8')
            file.close()
            file = open(file_path, 'wb')
            file.write(binary_f)
            file.close()

            product.name_of_photo = form.name.data + '_' + key + '.jpg'

            product.price = form.price.data
            product.description = form.description.data
            session.commit()
            categories = [i.strip() for i in form.categories.data.split('\n')]
            for category_name in categories:
                found_category = session.query(Category).\
                    filter(Category.name == category_name.strip()).first()
                if found_category:

                    product.categories.append(found_category)

                else:
                    new_category = Category(
                        name=category_name.strip()
                    )
                    session.add(new_category)
                    session.commit()

                    found_category = session.query(Category).\
                        filter(Category.name == category_name).first()
                    product.categories.append(found_category)
                    session.commit()
                for category in product.categories:
                    if category.name not in categories:
                        product.categories.remove(category)
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_product.html', title='Editing product', form=form)


@app.route('/add_to_basket/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_basket(id):
    session = db_session.create_session()
    product = session.query(Products).filter(Products.id == id).first()
    user = session.query(Users).filter(Users.id == current_user.id).first()
    if product:
        basket_now = session.query(Basket).filter(Basket.user_id == user.id,
                                                  Basket.product_id == id).first()
        if basket_now:
            basket_now.count += 1
        else:
            basket_now = Basket(user_id=user.id,
                                product_id=id,
                                count=1)
            session.add(basket_now)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
    global_init("db/shop.sqlite")
    session = db_session.create_session()
    user = session.query(Users).filter(Users.id == current_user.id).first()
    products = {}
    cost = 0
    for basket_now in user.basket:
        product = session.query(Products).filter(Products.id == basket_now.product_id).first()
        products[product] = basket_now.count
        cost += product.price * basket_now.count
    return render_template("basket.html", products=products, cost=cost)


@app.route('/basket_change_count/<int:id>/<int:count>', methods=['GET', 'POST'])
@login_required
def increase_decrease_count_of_product_in_basket(id, count):
    global_init("db/shop.sqlite")
    session = db_session.create_session()
    user = session.query(Users).filter(Users.id == current_user.id).first()
    products = {}
    cost = 0
    for basket_now in user.basket:
        product = session.query(Products).filter(Products.id == basket_now.product_id).first()
        if product.id == id:
            if count == 2:
                count = -1
            basket_now.count += count
            if basket_now.count < 1:
                basket_now.count = 1
            elif basket_now.count > 10:
                basket_now.count = 10
        session.commit()
        products[product] = basket_now.count
        cost += product.price * basket_now.count
    return render_template("basket.html", products=products, cost=cost)


@app.route('/product_page/<int:id>', methods=['GET', 'POST'])
def product_page(id):
    global_init("db/shop.sqlite")
    session = db_session.create_session()
    product = session.query(Products).filter(Products.id == id).first()
    categories = '\n'.join([category.name for category in product.categories])
    form = AddReview()
    if form.validate_on_submit():
        reviews = session.query(Reviews).filter(Reviews.product_id == id).all()
        reviews_list = []
        average_mark = 0
        for review_now in reviews:
            average_mark += int(review_now.mark)
            author = session.query(Users).filter(Users.id == review_now.user_id).first()
            reviews_list.append((author.email, review_now))
        if len(reviews) == 0:
            average_mark = 'Without reviews'
        else:
            average_mark /= len(reviews)
        if len(form.mark.data) != 1 or form.mark.data not in '12345':
            return render_template('product_page.html',
                                   form=form,
                                   message="Некорректная оценка", product=product,
                                   reviews=reviews_list, average_mark=average_mark,
                                   categories=categories)
        if form.review_field.data.count(' ') == len(form.review_field.data):
            return render_template('product_page.html',
                                   form=form,
                                   message="Пустой отзыв", product=product, reviews=reviews_list,
                                   average_mark=average_mark, categories=categories)
        user = session.query(Users).filter(Users.id == current_user.id).first()
        review_exist = session.query(Reviews).filter(Reviews.user_id == user.id).\
            filter(Reviews.product_id == id).first()
        if review_exist:
            review_exist.review = form.review_field.data
            review_exist.mark = form.mark.data
            return render_template('product_page.html',
                                   form=form, product=product,
                                   reviews=reviews_list, exist="Edit", average_mark=average_mark,
                                   categories=categories)
        review = Reviews(review=form.review_field.data,
                         mark=form.mark.data,
                         product_id=product.id,
                         user_id=user.id)
        session.add(review)
        session.commit()

    reviews = session.query(Reviews).filter(Reviews.product_id == id).all()
    reviews_list = []
    average_mark = 0
    for review_now in reviews:
        average_mark += int(review_now.mark)
        author = session.query(Users).filter(Users.id == review_now.user_id).first()
        reviews_list.append((author.email, review_now))
    if len(reviews) == 0:
        average_mark = 'Without reviews'
    else:
        average_mark /= len(reviews)
    exist = 'Add'
    if current_user.is_authenticated:
        user = session.query(Users).filter(Users.id == current_user.id).first()
        review_exist = session.query(Reviews).filter(Reviews.user_id == user.id).\
            filter(Reviews.product_id == id).first()
        if review_exist:
            exist = 'Edit'
            form.review_field.data = review_exist.review
            form.mark.data = review_exist.mark
    return render_template("product_page.html", product=product, reviews=reviews_list, form=form,
                           exist=exist, average_mark=average_mark, categories=categories)


@app.route('/basket_delete_product/<int:id>', methods=['GET', 'POST'])
@login_required
def basket_delete_product(id):
    session = db_session.create_session()
    user = session.query(Users).filter(Users.id == current_user.id).first()
    basket_to_delete = session.query(Basket).filter(Basket.product_id == id).\
        filter(Basket.user_id == user.id).first()
    if basket_to_delete:
        session.delete(basket_to_delete)
        session.commit()
    else:
        abort(404)
    products = {}
    cost = 0
    for basket_now in user.basket:
        product = session.query(Products).filter(Products.id == basket_now.product_id).first()
        products[product] = basket_now.count
        cost += product.price * basket_now.count
    return render_template("basket.html", products=products, cost=cost)


@app.route('/delete_review/<int:id>/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_review(id, product_id):
    session = db_session.create_session()
    review_to_delete = session.query(Reviews).filter(Reviews.id == id).first()
    if review_to_delete:
        session.delete(review_to_delete)
        session.commit()
    else:
        abort(404)
    return redirect(f'/product_page/{product_id}')


@app.route('/add_to_basket_from_product_page/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_basket_from_product_page(id):
    session = db_session.create_session()
    product = session.query(Products).filter(Products.id == id).first()
    user = session.query(Users).filter(Users.id == current_user.id).first()
    if product:
        basket_now = session.query(Basket).filter(Basket.user_id == user.id,
                                                  Basket.product_id == id).first()
        if basket_now:
            basket_now.count += 1
        else:
            basket_now = Basket(user_id=user.id,
                                product_id=id,
                                count=1)
            session.add(basket_now)
        session.commit()
    else:
        abort(404)
    return redirect(f'/product_page/{id}')


def main():
    global_init("db/shop.sqlite")
    app.run()


if __name__ == '__main__':
    main()
