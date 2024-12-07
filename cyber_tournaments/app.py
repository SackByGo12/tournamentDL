from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, join
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, TournamentForm
from uuid import uuid4

app = Flask(__name__)
app.config['SECRET_KEY'] = '101-546-966'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# инициализация базы данных
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)

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

class Tournament(db.Model, Base):
    __tablename__ = "tournaments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=True)
    creator_user_id = db.Column("creator_user_id", db.String(20), db.ForeignKey(User.id))

    @classmethod
    def get_tournament_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_tournaments_by_user_id(cls, user_id):
        return cls.query.filter_by(creator_user_id=user_id).all()
    
    @classmethod
    def create_tournament(cls, creator_user_id, name, description ):
        return cls(
            name=name,
            description=description or "",
            creator_user_id=creator_user_id,
        )
    
    @classmethod
    def edit_tournament(cls, id_tournament, new_tournament):
        tournament = Tournament.get_tournament_by_id(id_tournament)

        for col in Tournament.__table__.columns.keys():
            tournament[col] = new_tournament[col] or tournament[col]
        
        db.session.commit()

    def __repr__(self):
        return super().__repr__()

# Модель для связи многие ко многим между подписчиками и турнирами
class Tournament_participants(db.Model, Base):
    __tablename__ = 'tournament_participants'

    tournament_id = db.Column('tournament_id', db.ForeignKey('tournaments.id'), primary_key=True)
    user_id = db.Column('user_id', db.ForeignKey('users.id'))

    @classmethod
    def add_participants(cls, user_id, tournament_id):
        return cls(tournament_id=tournament_id, user_id=user_id)

with app.app_context():
    db.create_all()

# инициализация flask_login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(user_id)

# все шариковые ручки
@app.route('/')
def index():
    tournaments = Tournament.query\
        .join(User, Tournament.creator_user_id == User.id)\
        .add_columns(User.username, Tournament.id, Tournament.name, Tournament.description)\
        .all()
    
    return render_template('index.html', tournaments=tournaments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User.create_user(form.username.data, form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Вы успешно зарегистрировались!', 'success')

        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.get_user_by_username(form.username.data)

        if user and check_password_hash(user.password, form.password.data):
            login_user(user=user)

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
    tournaments = Tournament.get_tournaments_by_user_id(current_user.id)

    return render_template('dashboard.html', name=current_user.username, tournaments=tournaments)

@app.route('/create_tournament', methods=['GET', 'POST'])
@login_required
def create_tournament():
    form = TournamentForm()

    if form.validate_on_submit():
        tournament = Tournament.create_tournament(name=form.name.data, description=form.description.data, creator_user_id=current_user.id)

        db.session.add(tournament)
        db.session.commit()

        flash('Турнир успешно создан!', 'success')

        return redirect(url_for('dashboard'))
    
    return render_template('tournament.html', form=form)

@app.route('/join_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def join_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = Tournament_participants.query\
        .join(User, User.id == Tournament_participants.user_id)\
        .where(Tournament.id == Tournament_participants.tournament_id)\
        .add_columns(User.id)\
        .all()
    

    if current_user.id not in participants:
        new_participants = Tournament_participants.add_participants(current_user.id, tournament_id)

        db.session.add(new_participants)
        db.session.commit()
        flash(f'Вы присоединились к турниру "{tournament.name}"!', 'success')
    else:
        flash(f'Вы уже участвуете в турнире "{tournament.name}".', 'warning')

    print(participants)
    return redirect(url_for('index'))

@app.route('/delete_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if tournament.creator_user_id != current_user.id:
        flash('Вы не можете удалить этот турнир, так как вы не являетесь его создателем.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(tournament)
    db.session.commit()
    flash(f'Турнир "{tournament.name}" был удален.', 'success')
    return redirect(url_for('dashboard'))

# запуск приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)