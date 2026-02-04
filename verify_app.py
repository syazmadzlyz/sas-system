import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import create_app
    app = create_app('development')
    print("✅ App initialized successfully")
except Exception as e:
    print(f"❌ Error initializing app: {e}")
    import traceback
    traceback.print_exc()
