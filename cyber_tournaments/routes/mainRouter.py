from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.User import User
from models.Tournament import Tournament
from models.Tournament_participants import Tournament_participants

mainRouter = Blueprint("mainRouter", __name__)

@mainRouter.route('/')
@mainRouter.route('/index')
def index():
    tournaments = Tournament.query\
        .join(User, Tournament.creator_user_id == User.id)\
        .add_columns(User.username, Tournament.creator_user_id, Tournament.id, Tournament.name, Tournament.description)\
        .all()\
            
    is_participant_tournaments = User.query\
        .join(Tournament_participants, Tournament_participants.user_id == User.id)\
        .add_columns(Tournament_participants.tournament_id)\
        .all()\
            
    is_participant_tournaments = map(lambda tour: tour.tournament_id, is_participant_tournaments)
    
    return render_template('pages/index.html', tournaments=tournaments, is_participant_tournaments=is_participant_tournaments)

@mainRouter.route('/dashboard')
@login_required
def dashboard():
    tournaments = Tournament.get_tournaments_by_user_id(current_user.id)
    
    participant_tournaments = Tournament.get_participant_s_tournaments_by_user_id(current_user.id)

    return render_template('pages/dashboard.html',\
        name=current_user.username, tournaments=tournaments,\
        participant_tournaments=participant_tournaments\
    )
