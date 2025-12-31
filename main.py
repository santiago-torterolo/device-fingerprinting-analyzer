"""
Flask application entry point.
Initializes and runs the web server.
"""

import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        use_reloader=True
    )
