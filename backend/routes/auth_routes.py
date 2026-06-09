import datetime
from flask import Blueprint, request
from functools import wraps
from backend.services.firebase_service import firebase_service
from backend.utils.helpers import get_auth_token, success_response, error_response

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    """Decorator to require Firebase Authentication on endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_auth_token(request)
        if not token:
            return error_response("Authorization token is missing. Please log in.", 401)
            
        decoded_user = firebase_service.verify_id_token(token)
        if not decoded_user:
            return error_response("Invalid or expired authorization token.", 401)
            
        # Inject user data into the request object
        request.current_user = decoded_user
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Saves user credentials inside Firestore users collection.
    Payload: { uid, name, email }
    """
    data = request.get_json() or {}
    uid = data.get("uid")
    name = data.get("name")
    email = data.get("email")
    
    if not uid or not email or not name:
        return error_response("Fields 'uid', 'name', and 'email' are required.", 400)
        
    user_schema = {
        "uid": uid,
        "name": name,
        "email": email,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    success = firebase_service.set_document("users", uid, user_schema)
    if success:
        return success_response(user_schema, "User registered successfully.", 201)
    else:
        return error_response("Failed to store user profile in database.", 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Validates token and syncs user details.
    Uses ID token from Authorization header.
    """
    token = get_auth_token(request)
    if not token:
        return error_response("Authorization token is missing.", 401)
        
    decoded_user = firebase_service.verify_id_token(token)
    if not decoded_user:
        return error_response("Invalid or expired token.", 401)
        
    uid = decoded_user.get("uid")
    email = decoded_user.get("email")
    name = decoded_user.get("name", "Filmmaker")
    
    # Retrieve user or update info
    user_data = firebase_service.get_document("users", uid)
    if not user_data:
        # Create record if first-time social login
        user_data = {
            "uid": uid,
            "name": name,
            "email": email,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        firebase_service.set_document("users", uid, user_data)
        
    return success_response(user_data, "Login synchronized successfully.")

@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """Returns the authenticated user's profile information."""
    uid = request.current_user.get("uid")
    user_data = firebase_service.get_document("users", uid)
    if not user_data:
        return error_response("User profile not found.", 404)
        
    return success_response(user_data, "Profile retrieved successfully.")
