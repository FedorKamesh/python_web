from flask import Flask, redirect, render_template, jsonify, request
from flask_restful import abort

from form.DictForm import DictForm
from data import db_session, dicts_api
from data.users import User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from form.loginform import LoginForm
from data.diction import Dict
from flask import make_response

from form.registerform import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/writings',  methods=['GET', 'POST'])
@login_required
def add_dict():
    form = DictForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        dicts = Dict()
        dicts.title = form.title.data
        dicts.content = form.content.data
        dicts.is_private = form.is_private.data
        current_user.dicts.append(dicts)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('writings.html', title='Добавление записи',
                           form=form)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.route("/")
def index():
    db_sess = db_session.create_session()

    if current_user.is_authenticated:
        dicts = db_sess.query(Dict).filter(
            (Dict.user == current_user) | (Dict.is_private != True))
    else:
        dicts = db_sess.query(Dict).filter(Dict.is_private != True)
    return render_template("index.html", dicts=dicts)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,

        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/writings/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_writings(id):
    form = DictForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        dicts = db_sess.query(Dict).filter(Dict.id == id,
                                          Dict.user == current_user
                                          ).first()
        if dicts:
            form.title.data = dicts.title
            form.content.data = dicts.content
            form.is_private.data = dicts.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        dicts = db_sess.query(Dict).filter(Dict.id == id,
                                          Dict.user == current_user
                                          ).first()
        if dicts:
            dicts.title = form.title.data
            dicts.content = form.content.data
            dicts.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('writings.html',
                           title='Редактирование записи',
                           form=form
                           )
@app.route('/writings_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def writings_delete(id):
    db_sess = db_session.create_session()
    dicts = db_sess.query(Dict).filter(Dict.id == id,
                                      Dict.user == current_user
                                      ).first()
    if dicts:
        db_sess.delete(dicts)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(dicts_api.blueprint)
    app.run()

if __name__ == '__main__':
    main()