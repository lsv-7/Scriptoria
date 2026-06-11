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
        import threading
        self.lock = threading.RLock()
        self.db = None
        self.mock_mode = False
        self.mock_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_firestore_db.json")
        
        # In-memory database cache
        self.cache_get = {}
        self.cache_filter = {}
        
        self.initialize_firebase()

    def initialize_firebase(self):
        # Try loading credentials from raw JSON environment variable first
        creds_json_str = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if FIREBASE_AVAILABLE and creds_json_str:
            try:
                if not firebase_admin._apps:
                    creds_dict = json.loads(creds_json_str)
                    cred = credentials.Certificate(creds_dict)
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                print(">>> Firebase Admin initialized successfully using credentials JSON string from environment.")
                self.mock_mode = False
                return
            except Exception as e:
                print(f">>> Failed to initialize real Firebase Admin SDK from environment JSON: {e}. Trying file path next...")

        # Check if credential file exists
        creds_path = Config.FIREBASE_CREDENTIALS_PATH
        if FIREBASE_AVAILABLE and os.path.exists(creds_path):
            try:
                # Avoid re-initialization if app is already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                print(">>> Firebase Admin initialized successfully using service account JSON file.")
                self.mock_mode = False
            except Exception as e:
                print(f">>> Failed to initialize real Firebase Admin SDK: {e}. Falling back to Mock Firestore Mode.")
                self.setup_mock_mode()
        else:
            print(">>> Firebase credentials file/environment variable not found. Using Local Mock Firestore Mode.")
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
        In mock mode, accepts special mock tokens or returns None.
        """
        if not id_token:
            return None

        if self.mock_mode:
            # Mock Auth bypass for easy local testing - strictly requires mock_token_ prefix
            if id_token.startswith("mock_token_"):
                uid = id_token.replace("mock_token_", "")
            else:
                return None
            
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
        """Retrieves a single document by ID from collection (direct DB query, no local cache)."""
        doc = None
        if self.mock_mode:
            with self.lock:
                db_data = self._read_mock_db()
                coll_data = db_data.get(collection, {})
                doc = coll_data.get(doc_id)
        else:
            try:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_snap = doc_ref.get()
                doc = doc_snap.to_dict() if doc_snap.exists else None
            except Exception as e:
                print(f"Firestore get_document error on {collection}/{doc_id}: {e}")
                doc = None

        return doc

    def set_document(self, collection, doc_id, data):
        """Creates or overwrites a document by ID and updates/invalidates cache."""
        success = False
        if self.mock_mode:
            with self.lock:
                db_data = self._read_mock_db()
                if collection not in db_data:
                    db_data[collection] = {}
                # Handle datetime objects
                serializable_data = self._make_serializable(data)
                db_data[collection][doc_id] = serializable_data
                self._write_mock_db(db_data)
                success = True
        else:
            try:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.set(data)
                success = True
            except Exception as e:
                print(f"Firestore set_document error on {collection}/{doc_id}: {e}")
                success = False

        if success:
            with self.lock:
                self.cache_get[(collection, doc_id)] = dict(data) if data is not None else None
                # Invalidate all query filters for this collection
                keys_to_del = [k for k in self.cache_filter.keys() if k[0] == collection]
                for k in keys_to_del:
                    del self.cache_filter[k]
        return success

    def update_document(self, collection, doc_id, data):
        """Updates fields in an existing document and updates/invalidates cache."""
        success = False
        if self.mock_mode:
            with self.lock:
                db_data = self._read_mock_db()
                coll_data = db_data.get(collection, {})
                if doc_id in coll_data:
                    serializable_data = self._make_serializable(data)
                    coll_data[doc_id].update(serializable_data)
                    db_data[collection][doc_id] = coll_data[doc_id]
                    self._write_mock_db(db_data)
                    success = True
        else:
            try:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.update(data)
                success = True
            except Exception as e:
                print(f"Firestore update_document error on {collection}/{doc_id}: {e}")
                success = False

        if success:
            with self.lock:
                self.cache_get.pop((collection, doc_id), None)
                # Invalidate all query filters for this collection
                keys_to_del = [k for k in self.cache_filter.keys() if k[0] == collection]
                for k in keys_to_del:
                    del self.cache_filter[k]
        return success

    def delete_document(self, collection, doc_id):
        """Deletes a document by ID and invalidates cache."""
        success = False
        if self.mock_mode:
            with self.lock:
                db_data = self._read_mock_db()
                if collection in db_data and doc_id in db_data[collection]:
                    del db_data[collection][doc_id]
                    self._write_mock_db(db_data)
                    success = True
        else:
            try:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.delete()
                success = True
            except Exception as e:
                print(f"Firestore delete_document error on {collection}/{doc_id}: {e}")
                success = False

        if success:
            with self.lock:
                self.cache_get.pop((collection, doc_id), None)
                # Invalidate all query filters for this collection
                keys_to_del = [k for k in self.cache_filter.keys() if k[0] == collection]
                for k in keys_to_del:
                    del self.cache_filter[k]
        return success

    def get_documents_by_filter(self, collection, field, operator, value):
        """
        Retrieves documents matching a simple filter (direct DB query, no local cache).
        Only support '==' operator in mock mode.
        """
        results = []
        if self.mock_mode:
            with self.lock:
                db_data = self._read_mock_db()
                coll_data = db_data.get(collection, {})
                for doc_id, doc_fields in coll_data.items():
                    if field in doc_fields:
                        if operator == "==" and doc_fields[field] == value:
                            # Append key if not present in the doc fields
                            if "id" not in doc_fields and "project_id" not in doc_fields:
                                doc_fields["id"] = doc_id
                            results.append(doc_fields)
        else:
            try:
                docs = self.db.collection(collection).where(field, operator, value).stream()
                for doc in docs:
                    doc_data = doc.to_dict()
                    # Attach doc_id in results
                    if "id" not in doc_data:
                        doc_data["id"] = doc.id
                    results.append(doc_data)
            except Exception as e:
                print(f"Firestore query error on {collection}: {e}")

        return results

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
