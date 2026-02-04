"""
Application entry point for I-SAS - IIUM Student Assistant System
"""
import os
from app import create_app

# Get configuration from environment or use default
config_name = os.environ.get('FLASK_CONFIG') or 'development'

# Create application instance
app = create_app(config_name)

if __name__ == '__main__':
    # Run the development server
    port = int(os.environ.get('PORT', 5001))
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get DB URL for display
    db_url = os.environ.get('DATABASE_URL')
    masked_url = "SQLite (Local)"
    if db_url and 'postgresql' in db_url:
        # Mask password
        import re
        masked_url = re.sub(r':([^:@]+)@', ':****@', db_url)
        
    print(f"\n🏫 I-SAS - IIUM Student Assistant System v2.0.0")
    print(f"📍 Running at: http://localhost:{port}")
    print(f"🗄️  Database: {masked_url}")
    print(f"🔧 Mode: {config_name}\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )

