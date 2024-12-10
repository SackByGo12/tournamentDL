from app import db, Base
from models.User import User
from models.Tournament_participants import Tournament_participants

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
    def get_tournaments(cls):
        return cls.query.all()

    @classmethod
    def get_participant_s_tournaments_by_user_id(cls, user_id):
        is_participant_tournaments = User.query\
            .join(Tournament_participants, Tournament_participants.user_id == User.id)\
            .add_columns(Tournament_participants.tournament_id, User.id)\
            .where(User.id == user_id)\
            .all()\
                
        is_participant_tournament_ids = map(lambda tour: tour.tournament_id, is_participant_tournaments)
                
        tournaments = cls.get_tournaments()
                
        return list(filter(lambda tour: tour.id in is_participant_tournament_ids, tournaments))
    
    @classmethod
    def get_tournament_participants_by_tournament_id(cls, tournament_id):
        participants_of_tournament = Tournament_participants.query\
            .join(User, Tournament_participants.user_id == User.id)\
            .add_columns(Tournament_participants.tournament_id, User.id, User.username)\
            .where(Tournament_participants.tournament_id == tournament_id)\
            .all()\

        return participants_of_tournament

        
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
