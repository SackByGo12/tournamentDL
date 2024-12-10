from app import db, Base

class Tournament_participants(db.Model, Base):
    __tablename__ = 'tournament_participants'

    tournament_id = db.Column('tournament_id', db.ForeignKey('tournaments.id'), primary_key=True)
    user_id = db.Column('user_id', db.ForeignKey('users.id'))

    @classmethod
    def add_participants(cls, user_id, tournament_id):
        return cls(tournament_id=tournament_id, user_id=user_id)

    @classmethod
    def get_participant_by_user_id_and_tournament_id(cls, user_id, tournament_id):
        return cls.query.filter_by(user_id=user_id, tournament_id=tournament_id).first_or_404()

    @classmethod
    def delete_participants(cls, user_id, tournament_id):        
        result = cls.query\
            .filter_by(user_id=user_id, tournament_id=tournament_id)\
            .delete()
            
        db.session.commit()
        return result