from functools import wraps

import flask_admin
import flask_login
from flask import redirect, render_template, request, url_for
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from apps.competition.models import Users


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            # return redirect(url_for("admin/not_admin", next=request.url))
            return render_template("admin/not_admin.html")
        return f(*args, **kwargs)

    return decorated_function


class CompetitionsUpdateView(BaseView):
    @expose("/")
    @admin_required
    def index(self):
        return self.render("admin/update_competitions.html")


class CompetitionsRegisterView(BaseView):
    @expose("/")
    @admin_required
    def index(self):
        return self.render("admin/register_competitions.html")


def apply_admin(app, db):
    admin = Admin(
        app,
        index_view=MyAdminIndexView(),
        name="MyAdmin",
        template_mode="bootstrap4",
    )

    # admin = Admin(
    #     app, "管理者画面", index_view=MyAdminIndexView(), base_template="my_master.html"
    # )

    # admin.add_view(ModelView(Users, db.session))
    admin.add_view(
        CompetitionsUpdateView(
            name="Update Competition", endpoint="competitions/update"
        )
    )
    admin.add_view(
        CompetitionsRegisterView(
            name="Register Competition", endpoint="competitions/register"
        )
    )


class MyAdminIndexView(flask_admin.AdminIndexView):
    @expose("/")
    @admin_required
    def index(self):
        return super(MyAdminIndexView, self).index()


# init_login()
# admin = flask_admin.Admin(
#     app, "管理者画面", index_view=MyAdminIndexView(), base_template="my_master.html"
# )
# admin.add_view(MyModelView(AdminUser, db.session))
# admin.add_view(MyModelView(AdminUser, db.session))
