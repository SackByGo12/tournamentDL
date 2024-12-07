from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, TournamentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    # Отношение "один ко многим" — один пользователь может создать несколько турниров
    tournaments = db.relationship('Tournament', backref='creator', lazy=True)

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

class Tournament(db.Model):
    __tablename__ = "tournaments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=True)
    creator_user_id = db.Column("creator_user_id", db.Integer, db.ForeignKey(User.id))

    # Отношение "многие ко многим" — пользователи могут подписываться на турниры
    participants = db.ё (
        User.id, secondary='tournaments_participants', backref='joined_tournaments'
    )

    @classmethod
    def get_tournament_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_tournaments_by_username(cls, username):
        return cls.query.filter_by(username=username).scalar()
    
    @classmethod
    def create_tournament(cls, form, creator_user_id):
        return cls(
            name=form.get('name'),
            description=form.get('description'),
            creator_user_id=creator_user_id,
        )
    
    @classmethod
    def edit_tournament(cls, id_tournament, form):
        tournament = Tournament.get_tournament_by_id(id_tournament)

        tournament.name = form.get('name') or tournament.name
        tournament.description = form.get('description') or tournament.description
        tournament.participants = form.get('participants') or tournament.participants
        tournament.name = form.get('name') or tournament.name

    def __repr__(self):
        return super().__repr__()

# Модель для связи многие ко многим между пользователями и турнирами
tournament_participants = db.Table(
    'tournament_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('tournament_id', db.Integer, db.ForeignKey('tournament.id'), primary_key=True)
)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    tournaments = Tournament.query.all()
    return render_template('index.html', tournaments=tournaments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='scrypt')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)


@app.route('/create_tournament', methods=['GET', 'POST'])
@login_required
def create_tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(name=form.name.data, description=form.description.data, creator=current_user)
        db.session.add(tournament)
        db.session.commit()
        flash('Турнир успешно создан!', 'success')
        return redirect(url_for('index'))
    return render_template('tournament.html', form=form)

@app.route('/join_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def join_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if current_user not in tournament.participants:
        tournament.participants.append(current_user)
        db.session.commit()
        flash(f'Вы присоединились к турниру "{tournament.name}"!', 'success')
    else:
        flash(f'Вы уже участвуете в турнире "{tournament.name}".', 'warning')
    return redirect(url_for('index'))

@app.route('/delete_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if tournament.creator != current_user:
        flash('Вы не можете удалить этот турнир, так как вы не являетесь его создателем.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(tournament)
    db.session.commit()
    flash(f'Турнир "{tournament.name}" был удален.', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)