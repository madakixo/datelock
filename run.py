# run.py
from app import create_app, db
from app.models import User
from app.auth import init_oauth

app = create_app()
init_oauth(app)

with app.app_context():
    db.drop_all()
    db.create_all()
    # Create admin
    if not User.query.filter_by(email="admin@datelock.ng").first():
        admin = User(
            name="Admin", email="admin@datelock.ng",
            phone="08000000000", password=hash_password("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
    print("App ready!")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
