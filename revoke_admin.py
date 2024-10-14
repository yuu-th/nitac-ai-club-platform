from apps.authentication.models import Users
from run import app, db  # appオブジェクトをインポート


def revoke_admin_status(email):
    with app.app_context():
        user = Users.query.filter_by(email=email).first()
        if user:
            user.is_admin = False
            db.session.commit()
            print(f"User {email} is no longer an admin.")
        else:
            print(f"User {email} not found.")


# 例: ユーザーのメールアドレスを入力して管理者ステータスを剥奪
revoke_admin_status(
    input("Please input email of user you want to revoke admin status: ")
)
