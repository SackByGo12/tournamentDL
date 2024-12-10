from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.Dev')

# инициализация базы данных
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)

from models.User import User
from models.Tournament import Tournament
from models.Tournament_participants import Tournament_participants

with app.app_context():
    db.create_all()

# инициализация flask_login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authRouter.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(user_id)

# инициализация маршрутов
from routes.mainRouter import mainRouter
app.register_blueprint(mainRouter)

from routes.authRouter import authRouter
app.register_blueprint(authRouter)

from routes.tournamentRouter import tournamentRouter
app.register_blueprint(tournamentRouter)

# запуск приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)