import os
import json
import uuid
import datetime
from backend.config import Config

# Try to import firebase-admin. If it's not installed or setup fails, we'll fall back to local mock mode.
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

class FirebaseService:
    def __init__(self):
        self.db = None
        self.mock_mode = False
        self.mock_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_firestore_db.json")
        self.initialize_firebase()

    def initialize_firebase(self):
        # Check if credential file exists
        creds_path = Config.FIREBASE_CREDENTIALS_PATH
        if FIREBASE_AVAILABLE and os.path.exists(creds_path):
            try:
                # Avoid re-initialization if app is already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                print(">>> Firebase Admin initialized successfully using service account JSON.")
                self.mock_mode = False
            except Exception as e:
                print(f">>> Failed to initialize real Firebase Admin SDK: {e}. Falling back to Mock Firestore Mode.")
                self.setup_mock_mode()
        else:
            print(">>> Firebase credentials file not found or package not imported. Using Local Mock Firestore Mode.")
            self.setup_mock_mode()

    def setup_mock_mode(self):
        self.mock_mode = True
        self.db = None
        # Initialize the mock JSON database file if it doesn't exist
        if not os.path.exists(self.mock_db_path):
            self._write_mock_db({})

    def _read_mock_db(self):
        try:
            with open(self.mock_db_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_mock_db(self, data):
        try:
            with open(self.mock_db_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing to local mock database: {e}")

    # --- Authentication Helper ---
    def verify_id_token(self, id_token):
        """
        Verifies the Firebase Auth ID Token.
        In mock mode, accepts special mock tokens or returns placeholder user info.
        """
        if not id_token:
            return None

        if self.mock_mode:
            # Mock Auth bypass for easy local testing
            if id_token.startswith("mock_token_"):
                uid = id_token.replace("mock_token_", "")
            else:
                uid = "mock_user_123"
            
            # Retrieve or create mock user
            user_data = self.get_document("users", uid)
            if not user_data:
                user_data = {
                    "uid": uid,
                    "name": "Local Filmmaker",
                    "email": "filmmaker@cineforge.local",
                    "created_at": datetime.datetime.now().isoformat()
                }
                self.set_document("users", uid, user_data)
                
            return {
                "uid": uid,
                "name": user_data.get("name", "Local Filmmaker"),
                "email": user_data.get("email", "filmmaker@cineforge.local")
            }

        try:
            # Use real Firebase Auth validation
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying Firebase ID token: {e}")
            # If real firebase auth fails but we are testing locally, check if user provided a mock token anyway
            if id_token.startswith("mock_token_"):
                uid = id_token.replace("mock_token_", "")
                return {
                    "uid": uid,
                    "name": "Local Filmmaker (Bypassed)",
                    "email": "filmmaker@cineforge.local"
                }
            return None

    # --- Firestore CRUD Wrappers ---
    def get_document(self, collection, doc_id):
        """Retrieves a single document by ID from collection."""
        if self.mock_mode:
            db_data = self._read_mock_db()
            coll_data = db_data.get(collection, {})
            return coll_data.get(doc_id)

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Firestore get_document error on {collection}/{doc_id}: {e}")
            return None

    def set_document(self, collection, doc_id, data):
        """Creates or overwrites a document by ID."""
        if self.mock_mode:
            db_data = self._read_mock_db()
            if collection not in db_data:
                db_data[collection] = {}
            # Handle datetime objects
            serializable_data = self._make_serializable(data)
            db_data[collection][doc_id] = serializable_data
            self._write_mock_db(db_data)
            return True

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.set(data)
            return True
        except Exception as e:
            print(f"Firestore set_document error on {collection}/{doc_id}: {e}")
            return False

    def update_document(self, collection, doc_id, data):
        """Updates fields in an existing document."""
        if self.mock_mode:
            db_data = self._read_mock_db()
            coll_data = db_data.get(collection, {})
            if doc_id in coll_data:
                serializable_data = self._make_serializable(data)
                coll_data[doc_id].update(serializable_data)
                db_data[collection][doc_id] = coll_data[doc_id]
                self._write_mock_db(db_data)
                return True
            return False

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Firestore update_document error on {collection}/{doc_id}: {e}")
            return False

    def delete_document(self, collection, doc_id):
        """Deletes a document by ID."""
        if self.mock_mode:
            db_data = self._read_mock_db()
            if collection in db_data and doc_id in db_data[collection]:
                del db_data[collection][doc_id]
                self._write_mock_db(db_data)
                return True
            return False

        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Firestore delete_document error on {collection}/{doc_id}: {e}")
            return False

    def get_documents_by_filter(self, collection, field, operator, value):
        """
        Retrieves documents matching a simple filter.
        Only support '==' operator in mock mode.
        """
        if self.mock_mode:
            db_data = self._read_mock_db()
            coll_data = db_data.get(collection, {})
            results = []
            for doc_id, doc_fields in coll_data.items():
                if field in doc_fields:
                    if operator == "==" and doc_fields[field] == value:
                        # Append key if not present in the doc fields
                        if "id" not in doc_fields and "project_id" not in doc_fields:
                            doc_fields["id"] = doc_id
                        results.append(doc_fields)
            return results

        try:
            docs = self.db.collection(collection).where(field, operator, value).stream()
            results = []
            for doc in docs:
                doc_data = doc.to_dict()
                # Attach doc_id in results
                if "id" not in doc_data:
                    doc_data["id"] = doc.id
                results.append(doc_data)
            return results
        except Exception as e:
            print(f"Firestore query error on {collection}: {e}")
            return []

    def _make_serializable(self, data):
        """Converts datetime objects in a dictionary to string format."""
        if not isinstance(data, dict):
            return data
            
        new_data = {}
        for k, v in data.items():
            if isinstance(v, (datetime.datetime, datetime.date)):
                new_data[k] = v.isoformat()
            elif isinstance(v, dict):
                new_data[k] = self._make_serializable(v)
            elif isinstance(v, list):
                new_data[k] = [self._make_serializable(item) if isinstance(item, dict) else item for item in v]
            else:
                new_data[k] = v
        return new_data

# Instantiate service singleton
firebase_service = FirebaseService()
