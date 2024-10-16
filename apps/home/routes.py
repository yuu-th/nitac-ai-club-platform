# -*- encoding: utf-8 -*-

"""
Copyright (c) 2019 - present AppSeed.us
"""

import threading
from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

from apps import db
from apps.competition.models import (
    Competitions,
    DifficultyEnum,
    Users,
    user_competition,
)
from apps.home import blueprint
from kaggle_utils import calc_result_list

from .utils import calc_local_position, calc_rating, calc_total_rating


@blueprint.route("/index")
@login_required
def index():
    # return render_template("blueprint_home.ranking", segment="index")
    return ranking()
    return render_template("home/index.html", segment="index")


# def load_all_competitions():
#     return [
#         {
#             "name": "Argon Design System",
#             "url": "competitions/1",
#             "difficulty": "easy",
#             "n_achiever": 10,
#             "users": [
#                 "team-1-800x800.jpg",
#                 "team-2-800x800.jpg",
#                 "team-3-800x800.jpg",
#                 "team-4-800x800.jpg",
#             ],
#             "image": "angular.jpg",
#             "your_best_score": 0.95,
#             "your_local_position": 2,
#         },
#     ]


def load_all_competitions():
    competitions = Competitions.query.all()
    result = []

    for competition in competitions:
        users = [user.image for user in competition.users if user.image is not None]
        your_best_score = None
        your_local_position = None

        for user in competition.users:
            if user.id == current_user.id:
                record = (
                    db.session.query(user_competition)
                    .filter_by(user_id=user.id, competition_id=competition.id)
                    .first()
                )
                if record:
                    your_best_score = record.best_score
                    your_local_position = (
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

        result.append(
            {
                "name": competition.name,
                "url": f"competitions/{competition.id}",
                "difficulty": competition.difficulty.value,
                "n_achiever": competition.get_achievers_count(),
                "users": users,
                "image": competition.image,
                "your_best_score": your_best_score,
                "your_local_position": your_local_position,
            }
        )

    return result


@blueprint.route("/available_competitions")
@login_required
def available_competitions():
    competitions = load_all_competitions()
    if competitions is None:
        return render_template("home/page-404.html"), 404
    return render_template(
        "home/available_competitions.html", competitions=competitions
    )


def load_all_users():
    users = Users.query.all()
    result = []

    for position, user in enumerate(users, start=1):
        n_achieved = len(user.competitions)
        n_authenticated_achieved = sum(
            1 for comp in user.competitions if comp.is_authenticated
        )

        result.append(
            {
                "position": position,
                "name": user.username,
                "url": f"/users/{user.id}",
                "user_image": user.image,
                "rating": user.rating,  # Replace with actual rate if available
                "n_achieved": n_achieved,
                "n_authenticated_achieved": n_authenticated_achieved,
            }
        )

    return result


@blueprint.route("/ranking")
@login_required
async def ranking():
    await update_timeout_users_rating(60)
    users = load_all_users()
    if users is None:
        return render_template("home/page-404.html"), 404

    return render_template("home/ranking.html", user_data=users)


def load_competition_list_user_participated(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return []

    result = []

    for competition in user.competitions:
        record = (
            db.session.query(user_competition)
            .filter_by(user_id=user.id, competition_id=competition.id)
            .first()
        )

        if record:
            result.append(
                {
                    "name": competition.name,
                    "image": competition.image,
                    "url": f"competitions/{competition.id}",
                    "difficulty": competition.difficulty.value,
                    "n_achiever": competition.get_achievers_count(),
                    "additional_rating": calc_rating(user, competition, record),
                    "notebook_url": record.notebook_link,
                    "updated_time": record.last_updated_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if record.last_updated_time
                    else None,
                    "best_score": record.best_score,
                    "local_rank": calc_local_position(competition, user, db),
                }
            )

    return result


def load_user_detail(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return None

    return {
        "profile_image": user.image,  # Replace with actual path
        "user_name": user.username,  # Replace with actual user name
        "rating": user.rating,  # Replace with actual rating
    }


@blueprint.route("/users/<string:user_id>")
@login_required
def user_detail(user_id):
    try:
        # Detect the current page
        segment = get_segment(request)

        # Fetch user details from the database or any other source
        # user_details = {
        #     "profile_image": "path/to/profile/image.jpg",  # Replace with actual path
        #     "user_name": "test name",  # Replace with actual user name
        #     "rating": 1040,  # Replace with actual rating
        # }

        await update_user_rating_if_timeout(user_id, 60)
        user_details = load_user_detail(user_id)
        if user_details is None:
            return render_template("home/page-404.html"), 404

        # Serve the user.html file with user details
        return render_template(
            "home/user.html",
            segment=segment,
            user_id=user_id,
            **user_details,
            user_competition_list=load_competition_list_user_participated(user_id),
        )

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except Exception as e:
        print(e)
        return render_template("home/page-500.html"), 500


@blueprint.route("/my_profile")
@login_required
def my_profile():
    # user_idをloginのセッション情報から
    user_id = current_user.id
    return user_detail(user_id)


def load_user_score(competition_id):
    user_id = current_user.id
    record = (
        db.session.query(user_competition)
        .filter_by(user_id=user_id, competition_id=competition_id)
        .first()
    )
    competition = Competitions.query.filter_by(id=competition_id).first()
    user = Users.query.filter_by(id=user_id).first()

    if record is None:
        return []

    return {
        "notebook_url": record.notebook_link,
        "updated_time": record.last_updated_time.strftime("%Y-%m-%d %H:%M:%S")
        if record.last_updated_time
        else None,
        "best_score": record.best_score,
        "local_rank": calc_local_position(competition, user, db),
    }


def load_local_user_ranking(competition_id):
    competition = Competitions.query.get(competition_id)
    if competition is None:
        return None

    records = (
        db.session.query(user_competition)
        .filter_by(competition_id=competition_id)
        .order_by(user_competition.c.best_score.desc())
        .all()
    )

    data = []
    for position, record in enumerate(records, start=1):
        user = Users.query.get(record.user_id)
        if user is None:
            continue
        data.append(
            {
                "image": user.image,
                "user": user.username,
                "position": position,
                "score": record.best_score,
                "notebook_link": record.notebook_link,
            }
        )

    return data


def load_competition(competition_id):
    competition = Competitions.query.get(competition_id)
    if competition is None:
        return None

    result = {
        "id": str(competition.id),
        "name": competition.name,
        "description": competition.notes,
        "difficulty": competition.difficulty.value,
        "references": [
            {
                "url": ref.get("url"),
                "comment": ref.get("comment"),
            }
            for ref in competition.resources
        ],
        "templates": [
            {
                "url": tmpl.get("url"),
                "comment": tmpl.get("comment"),
            }
            for tmpl in competition.template_urls
        ],
        "notes": competition.notes,
    }

    return result


@blueprint.route("/competitions/<string:competition_id>")
@login_required
def competition_detail(competition_id):
    try:
        # Detect the current page
        segment = get_segment(request)

        competition = load_competition(competition_id)
        if competition is None:
            return render_template("home/page-404.html"), 404
        user_result = load_user_score(competition_id)
        if user_result is None:
            return render_template("home/page-404.html"), 404
        local_user_ranking = load_local_user_ranking(competition_id)
        if local_user_ranking is None:
            return render_template("home/page-404.html"), 404

        # Serve the competition.html file
        return render_template(
            "home/competition.html",
            segment=segment,
            # competition_id=competition_id,
            competition=competition,
            user_result=user_result,
            local_user_ranking=local_user_ranking,
        )

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    # except:
    #     return render_template("home/page-500.html"), 500


# def load_all_competitions():
#     competitions = Competitions.query.all()
#     result = []

#     for competition in competitions:
#         result.append(
#             {
#                 "id": str(competition.id),
#                 "name": competition.name,
#                 "description": competition.notes,
#                 "difficulty": competition.difficulty.value,
#                 "references": [
#                     {
#                         "url": ref.get("url"),
#                         "comment": ref.get("comment"),
#                     }
#                     for ref in competition.resources.get("references", [])
#                 ],
#                 "templates": [
#                     {
#                         "url": tmpl.get("url"),
#                         "comment": tmpl.get("comment"),
#                     }
#                     for tmpl in competition.template_urls
#                 ],
#                 "notes": competition.notes,
#             }
#         )

#     return result


@blueprint.route("/update_competition_score", methods=["POST"])
def update_my_competition_score():
    return update_competition_score(current_user.id)


@blueprint.route("/update_competition_score/<string:user_id>", methods=["POST"])
def update_competition_score(user_id):
    user = Users.query.filter_by(id=user_id).first()
    if user is None:
        return jsonify({"status": "failed", "message": "User not found"}), 404

    if user.user_name_in_kaggle is None:
        return (
            jsonify(
                {"status": "failed", "message": "Kaggle user name is not registered"}
            ),
        )

    try:
        result_list = calc_result_list(user.user_name_in_kaggle)
    except Exception as e:
        return jsonify(
            {
                "status": "failed",
                "message": f"Error fetching competition results: {str(e)}",
            }
        ), 500
    if len(result_list) == 0:
        return jsonify({"status": "failed", "message": "No results found"}), 400

    changes_made = False

    for result in result_list:
        competition = Competitions.query.filter_by(name=result.competition_url).first()
        if competition is None:
            competition = Competitions(
                name=result.competition_url,
                difficulty=DifficultyEnum["EASY"],
                is_authenticated=False,
            )
            db.session.add(competition)
            changes_made = True

        user_competition_record = (
            db.session.query(user_competition)
            .filter_by(user_id=user.id, competition_id=competition.id)
            .first()
        )

        if user_competition_record is None:
            insert_stmt = user_competition.insert().values(
                user_id=user.id,
                competition_id=competition.id,
                best_score=result.score,
                notebook_link=result.code_url,
            )
            db.session.execute(insert_stmt)
            changes_made = True
        else:
            if (
                user_competition_record.best_score != result.score
                or user_competition_record.notebook_link != result.code_url
            ):
                update_stmt = (
                    user_competition.update()
                    .where(
                        (user_competition.c.user_id == user.id)
                        & (user_competition.c.competition_id == competition.id)
                    )
                    .values(
                        best_score=result.score,
                        notebook_link=result.code_url,
                        last_updated_time=datetime.now(),
                    )
                )
                db.session.execute(update_stmt)
                changes_made = True
            else:
                update_stmt = (
                    user_competition.update()
                    .where(
                        (user_competition.c.user_id == user.id)
                        & (user_competition.c.competition_id == competition.id)
                    )
                    .values(last_updated_time=datetime.now())
                )
                db.session.execute(update_stmt)

    try:
        db.session.commit()
        try:
            update_rating(user.id)
        except Exception as e:
            return jsonify(
                {
                    "status": "failed",
                    "message": f"Error updating rating: {str(e)}",
                }
            ), 500
        if changes_made:
            return jsonify(
                {"status": "success", "message": "Competitions updated successfully"}
            ), 200
        else:
            return jsonify(
                {"status": "success", "message": "No changes made to competitions"}
            ), 204
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"status": "failed", "message": f"Error updating competitions: {str(e)}"}
        ), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


@login_required
@blueprint.route("/profile")
def profile():
    return render_template("home/profile.html", segment="profile")


@blueprint.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    data = request.form
    username = data.get("username")
    kaggle_username = data.get("kaggle_username")

    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400

    user = Users.query.get(current_user.id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    user.username = username
    user.user_name_in_kaggle = kaggle_username

    try:
        db.session.commit()
        return jsonify(
            {"status": "success", "message": "Profile updated successfully"}
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"status": "error", "message": f"Error updating profile: {str(e)}"}
        ), 500


# @login_required
# @blueprint.route("/update_rating", methods=["POST"])
# def update_my_rating():
#     return update_rating(current_user.id)


# @login_required
# @blueprint.route("/update_rating/<string:user_id>", methods=["POST"])
def update_rating(user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    user.rating = calc_total_rating(user)

    try:
        db.session.commit()
        return jsonify(
            {"status": "success", "message": "Rating updated successfully"}
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"status": "error", "message": f"Error updating rating: {str(e)}"}
        ), 500


async def update_timeout_users_rating(min_timeout_seconds=60 * 60 * 24):
    min_timeout_delta = timedelta(seconds=min_timeout_seconds)
    users = Users.query.all()
    for user in users:
        last_updated_times = [
            db.session.query(user_competition)
            .filter_by(user_id=user.id, competition_id=competition.id)
            .first()
            .last_updated_time
            for competition in user.competitions
        ]

        if len(last_updated_times) > 0 and last_updated_times[0] is not None:
            last_updated_time = max(last_updated_times)
            print(last_updated_times)
            if datetime.now() - last_updated_time > min_timeout_delta:
                update_competition_score(user.id)


async def update_user_rating_if_timeout(user_id, min_timeout_seconds=60 * 60 * 24):
    user = db.session.query(Users).filter_by(id=user_id).first()
    min_timeout_delta = timedelta(seconds=min_timeout_seconds)
    last_updated_times = [
        db.session.query(user_competition)
        .filter_by(user_id=user_id, competition_id=competition.id)
        .first()
        .last_updated_time
        for competition in user.competitions
    ]

    if len(last_updated_times) > 0 and last_updated_times[0] is not None:
        last_updated_time = max(last_updated_times)
        print(last_updated_times)
        if datetime.now() - last_updated_time > min_timeout_delta:
            update_competition_score(user_id)


@login_required
@blueprint.route("/<template>")
def route_template(template):
    try:
        if not template.endswith(".html"):
            template += ".html"

        segment = get_segment(request)

        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404
    except Exception as e:
        print(e)
        return render_template("home/page-500.html"), 500
    except TemplateNotFound:
        return render_template("home/page-404.html"), 404
    except Exception as e:
        print(e)
        return render_template("home/page-500.html"), 500
    except TemplateNotFound:
        return render_template("home/page-404.html"), 404
    except Exception as e:
        print(e)
        return render_template("home/page-500.html"), 500
        return render_template("home/page-500.html"), 500
