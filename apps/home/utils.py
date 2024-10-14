from apps.competition.models import user_competition


def calc_additional_rating(best_score: float):
    if best_score is None:
        return 0
    if best_score >= 0.95:
        return 100
    elif best_score >= 0.9:
        return 50
    elif best_score >= 0.85:
        return 30
    elif best_score >= 0.8:
        return 20
    elif best_score >= 0.75:
        return 10


def calc_local_position(competition, user, db):
    return (
        sorted(
            competition.users,
            key=lambda u: db.session.query(user_competition)
            .filter_by(user_id=u.id, competition_id=competition.id)
            .first()
            .best_score,
            reverse=True,
        ).index(user)
        + 1
    )
