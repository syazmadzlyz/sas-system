"""
Script to migrate database for Password Reset System
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    print("❌ No DATABASE_URL found")
    exit(1)

# Fix potential postgres://
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL)

def run_migration():
    print(f"🔄 Connecting to database...")
    
    with engine.connect() as conn:
        # Add columns to users table
        print(">> Adding reset columns to users table...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_requested BOOLEAN DEFAULT FALSE"))
            print("   ✅ Added reset_requested")
        except Exception as e:
            print(f"   ⚠️  reset_requested might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_approved BOOLEAN DEFAULT FALSE"))
            print("   ✅ Added reset_approved")
        except Exception as e:
            print(f"   ⚠️  reset_approved might exist: {e}")
            
        conn.commit()
    
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    run_migration()
