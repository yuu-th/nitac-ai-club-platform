from apps import db
from apps.competition.models import (Competitions, DifficultyEnum, Users,
                                     user_competition)


def calc_total_rating(user: Users):
    rating = 0
    for competition in user.competitions:
        record = (
            db.session.query(user_competition)
            .filter_by(user_id=user.id, competition_id=competition.id)
            .first()
        )
        if record is None:
            assert False

        rating += calc_rating(user, competition, record)

    return rating


def calc_rating(user, competition, record):
    best_score = record.best_score
    if best_score is None:
        assert False

    if competition.is_authenticated:
        if competition.difficulty== DifficultyEnum.EASY:
            base_point = 10
        elif competition.difficulty== DifficultyEnum.MEDIUM:
            base_point = 20
        elif competition.difficulty== DifficultyEnum.HARD:
            base_point = 30
    else:
        base_point = 10

    if best_score >= 0.96:
        return 8 * base_point
    elif best_score >= 0.93:
        return 7 * base_point
    elif best_score >= 0.9:
        return 6 * base_point
    elif best_score >= 0.85:
        return 5 * base_point
    elif best_score >= 0.8:
        return 4 * base_point
    elif best_score >= 0.7:
        return 3 * base_point
    elif best_score >= 0.5:
        return 2 * base_point
    else:
        return 0


# def calc_additional_rating(best_score: float):
#     if best_score is None:
#         return 0
#     if best_score >= 0.95:
#         return 100
#     elif best_score >= 0.9:
#         return 50
#     elif best_score >= 0.85:
#         return 30
#     elif best_score >= 0.8:
#         return 20
#     elif best_score >= 0.75:
#         return 10


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
            .best_score,
            reverse=True,
        ).index(user)
        + 1
    )
