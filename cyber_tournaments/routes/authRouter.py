from flask import Blueprint, flash, url_for, redirect, render_template
from flask_login import login_user, logout_user, login_required
from forms import RegistrationForm, LoginForm
from werkzeug.security import check_password_hash

from app import db
from models.User import User

authRouter = Blueprint("authRouter", __name__)

@authRouter.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        existUser = User.get_user_by_username(form.username.data)
        if(existUser):
            flash('Имя пользователя уже занято', category='error')
            return render_template('pages/register.html', form=form)
        
        user = User.create_user(form.username.data, form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Вы успешно зарегистрировались!', 'success')

        return redirect(url_for('authRouter.login'))
    
    return render_template('pages/register.html', form=form)

@authRouter.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.get_user_by_username(form.username.data)

        if user and check_password_hash(user.password, form.password.data):
            login_user(user=user)

            return redirect(url_for('mainRouter.dashboard'))
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')

    return render_template('pages/login.html', form=form)

@authRouter.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('mainRouter.index'))
