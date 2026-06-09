import os
import sys

# Python 3.14 compatibility workaround for protobuf C-extension metaclass changes
sys.modules['google._upb._message'] = None

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Config:
    # Flask config
    SECRET_KEY = os.environ.get("SECRET_KEY", "cineforge_ai_secret_key_123456")
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    PORT = int(os.environ.get("PORT", 5001))

    # Firebase Configuration
    # Can point to a local JSON file for the service account
    FIREBASE_CREDENTIALS_PATH = os.environ.get(
        "FIREBASE_CREDENTIALS_PATH", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "firebase_creds.json")
    )
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # IBM Watsonx AI (Granite model) Configuration
    WATSONX_API_KEY = os.environ.get("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID = os.environ.get("WATSONX_PROJECT_ID", "")
    # Default endpoint URL for US South (Dallas) region. Customize as needed.
    WATSONX_URL = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_MODEL_ID = os.environ.get("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")
