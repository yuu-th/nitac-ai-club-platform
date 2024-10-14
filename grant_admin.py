from apps.competition.models import Users
from run import app, db  # appオブジェクトをインポート


def grant_admin_status(email):
    with app.app_context():
        user = Users.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"User {email} is now an admin.")
        else:
            print(f"User {email} not found.")


# 例: ユーザーのメールアドレスを入力して管理者ステータスを付与
grant_admin_status(input("Please input email of user you want to grant admin status: "))
