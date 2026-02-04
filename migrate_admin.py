"""
Script to migrate database for Admin System
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
        # 1. Add columns to users table
        print(">> Adding columns to users table...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
            print("   ✅ Added is_admin")
        except Exception as e:
            print(f"   ⚠️  is_admin might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE"))
            print("   ✅ Added is_blocked")
        except Exception as e:
            print(f"   ⚠️  is_blocked might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()"))
            print("   ✅ Added last_seen")
        except Exception as e:
            print(f"   ⚠️  last_seen might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN warning_count INTEGER DEFAULT 0"))
            print("   ✅ Added warning_count")
        except Exception as e:
            print(f"   ⚠️  warning_count might exist: {e}")

        # 2. Create announcements table
        print(">> Creating announcements table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id SERIAL PRIMARY KEY,
                    message VARCHAR(500) NOT NULL,
                    type VARCHAR(20) DEFAULT 'info',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    user_id INTEGER NOT NULL REFERENCES users(id)
                )
            """))
            print("   ✅ Created announcements table")
        except Exception as e:
            print(f"   ❌ Error creating announcements: {e}")
            
        conn.commit()
    
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    run_migration()
