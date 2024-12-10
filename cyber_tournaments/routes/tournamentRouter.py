from flask import Blueprint, flash, url_for, redirect, render_template
from flask_login import login_required, current_user
from forms import TournamentForm

from app import db
from models.User import User
from models.Tournament import Tournament
from models.Tournament_participants import Tournament_participants

tournamentRouter = Blueprint("tournamentRouter", __name__)

@tournamentRouter.route('/tournament/<int:tournament_id>', methods=["GET"])
def tournament(tournament_id):
    tour = Tournament.get_tournament_by_id(tournament_id)
    participants = Tournament.get_tournament_participants_by_tournament_id(tournament_id)

    is_participant_tournaments = User.query\
        .join(Tournament_participants, Tournament_participants.user_id == User.id)\
        .add_columns(Tournament_participants.tournament_id)\
        .all()
    is_participant_tournaments = map(lambda tour: tour.tournament_id, is_participant_tournaments)

        
    return render_template('pages/tournament.html', tournament=tour, participants=participants, is_participant_tournaments=is_participant_tournaments)

@tournamentRouter.route('/create_tournament', methods=['GET', 'POST'])
@login_required
def create_tournament():
    form = TournamentForm()

    if form.validate_on_submit():
        tournament = Tournament.create_tournament(name=form.name.data, description=form.description.data, creator_user_id=current_user.id)

        db.session.add(tournament)
        db.session.commit()

        flash('Турнир успешно создан!', 'success')

        return redirect(url_for('mainRouter.dashboard'))
    
    return render_template('pages/create_tournament.html', form=form)

@tournamentRouter.route('/join_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def join_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = Tournament_participants.query\
        .join(User, User.id == Tournament_participants.user_id)\
        .where(Tournament.id == Tournament_participants.tournament_id)\
        .add_columns(User.id)\
        .all()

    if current_user.id not in map(lambda participant: participant.id, participants):
        new_participants = Tournament_participants\
            .add_participants(user_id=current_user.id, tournament_id=tournament_id)

        db.session.add(new_participants)
        db.session.commit()
        flash(f'Вы присоединились к турниру "{tournament.name}"!', 'success')
    else:
        flash(f'Вы уже участвуете в турнире "{tournament.name}".', 'warning')

    return redirect(url_for('mainRouter.index'))

@tournamentRouter.route('/delete_tournament/<int:tournament_id>', methods=['POST'])
@login_required
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if tournament.creator_user_id != current_user.id:
        flash('Вы не можете удалить этот турнир, так как вы не являетесь его создателем.', 'danger')
        return redirect(url_for('mainRouter.dashboard'))
    
    db.session.delete(tournament)
    db.session.commit()
    flash(f'Турнир "{tournament.name}" был удален.', 'success')
    return redirect(url_for('mainRouter.dashboard'))

@tournamentRouter.route('/remove_participant/<int:tournament_id>', methods=['POST'])
@login_required
def remove_participant(tournament_id):
    tour = Tournament.get_tournament_by_id(tournament_id)
    
    Tournament_participants.delete_participants(current_user.id, tournament_id)
    
    flash(f'Вы были отписаны от турнира "{tour.name}".', 'success')
    return redirect(url_for('mainRouter.dashboard'))
