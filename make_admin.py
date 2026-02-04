"""
Script to make a user an Admin
"""
import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from models.database import User

app = create_app()

def make_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found.")
            return
        
        user.is_admin = True
        db.session.commit()
        print(f"✅ User '{username}' is now an ADMIN.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <username>")
    else:
        make_admin(sys.argv[1])
