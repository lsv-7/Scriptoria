# CineForge AI: Pre-Production Studio Setup Guide & API Documentation

CineForge AI is a film pre-production studio web application. This guide details how to install dependencies, configure credentials, boot the servers, and interface with the API.

---

## 1. Directory Structure

```
Scriptoria_1/
├── backend/
│   ├── app.py                      # Flask Server Entrypoint
│   ├── config.py                   # Environment & Configuration Loader
│   ├── requirements.txt            # Python Dependencies
│   ├── firebase_creds.json         # [PLACEHOLDER] Place Firebase service account JSON here
│   ├── routes/
│   │   ├── auth_routes.py          # Session sync and Profile routes
│   │   ├── project_routes.py       # Projects CRUD operations
│   │   ├── story_routes.py         # Story Analysis & Structure generators
│   │   ├── screenplay_routes.py    # Screenplay script generator (IBM Granite)
│   │   ├── character_routes.py     # Character designer profiles (Gemini)
│   │   ├── scene_routes.py         # Scene Breakdown generator (Gemini)
│   │   ├── storyboard_routes.py    # Storyboard prompts deck (Gemini)
│   │   ├── sound_routes.py         # Sound Design planners (IBM Granite)
│   │   └── production_routes.py    # Production and Logistics scheduler (IBM Granite)
│   ├── services/
│   │   ├── firebase_service.py     # Firebase SDK and local JSON Mock DB
│   │   ├── gemini_service.py       # Google Gemini API client
│   │   ├── granite_service.py      # IBM Watsonx text generation client
│   │   └── export_service.py       # ReportLab PDF, DOCX, & TXT compilers
│   └── utils/
│       ├── prompts.py              # Engineered prompting templates
│       ├── validators.py           # Inputs sanitization & rules checker
│       └── helpers.py              # JSON cleaners & general helpers
├── frontend/
│   ├── index.html                  # Single Page Application HTML shell
│   ├── css/
│   │   └── style.css               # Cinematic CSS Styling & Reel loaders
│   └── js/
│       ├── api.js                  # Axios/Fetch backend communication layer
│       ├── auth.js                 # Firebase Auth & Demo Mode hooks
│       └── app.js                  # SPA route managers & dynamic UI compilers
├── verify_api.py                   # Verification suite integration script
└── setup_guide.md                  # Setup guidelines (This file)
```

---

## 2. Setup & Installation

### Step A: Install Dependencies
Open a terminal inside the `backend/` directory and install the Python packages:
```bash
pip install -r requirements.txt
```

### Step B: Environment Variables (`.env`)
Create a file named `.env` in the `backend/` directory and fill in the following variables:
```env
# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
SECRET_KEY=your_cineforge_secret_signing_key_here

# Firebase Settings
# Point to your Firebase admin service account JSON credentials
FIREBASE_CREDENTIALS_PATH=firebase_creds.json

# AI Model Keys
GEMINI_API_KEY=your_google_gemini_api_key_here
WATSONX_API_KEY=your_ibm_cloud_iam_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_guid_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

### Step C: Local Test Running (Without API Keys)
CineForge AI has a built-in **Demo Mode** / **Mock Fallback** for both authentication and AI generators. If you run the server without configuring credentials:
- The backend will write to a local JSON file: `backend/local_firestore_db.json`.
- The generators will produce realistic, pre-production templates dynamically.
- The exporters will build PDFs and Word documents correctly.

---

## 3. Running the Application

### 1. Launch the Backend Server
Run the Flask server from the `backend/` folder:
```bash
python app.py
```
The console will boot on `http://localhost:5000`.

### 2. Launch the Frontend
You can open `frontend/index.html` directly in any web browser (`file:///path/to/frontend/index.html`), or serve it using a lightweight local server (e.g. `npx serve` or Python's HTTP server):
```bash
# In the frontend directory:
python -m http.server 8000
```
Then visit `http://localhost:8000`.

---

## 4. Firebase Console Setup

To connect your own Firebase environment instead of using the local Demo Mode:

1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/) and click "Create a Project".
2. **Enable Firestore Database**:
   - In the sidebar, click **Build > Firestore Database** and click "Create database". Start in Test mode.
3. **Enable Firebase Authentication**:
   - Click **Build > Authentication > Get Started**.
   - Enable **Email/Password** provider.
   - Enable **Google** sign-in provider.
4. **Get Frontend Client Configuration**:
   - Go to **Project Settings > General** and click the web icon `</>` to register a web app.
   - Copy the configuration object and paste it inside [frontend/js/auth.js](file:///c:/Users/wwwlo/Downloads/College/Scriptoria_1/frontend/js/auth.js) replacing `firebaseConfig`.
5. **Get Backend Admin SDK Service Account JSON**:
   - Go to **Project Settings > Service Accounts**.
   - Click **Generate new private key** to download a JSON file.
   - Save this file inside `backend/` as `firebase_creds.json`.

---

## 5. API Endpoints Reference

All endpoints expect bearer tokens in the authorization header: `Authorization: Bearer <TOKEN>`.

### Authentication
- `POST /signup`
  - Payload: `{"uid": "user_id_123", "name": "Nolan", "email": "nolan@studio.com"}`
  - Response: Saves profile details to Firestore.
- `POST /login`
  - Syncs the authentication tokens. Returns user schema details.
- `GET /profile`
  - Returns user profile fields.

### Project CRUD
- `POST /create-project`
  - Payload: `{"project_name": "Inception", "genre": "Sci-Fi", "target_audience": "YA", "story_idea": "Dream thieves..."}`
  - Response: Creates a new project in Firestore.
- `GET /projects`
  - Returns list of user projects.
- `GET /project/<id>`
  - Returns project metadata and compiles all associated pre-production module details (Story Analysis, Screenplays, Scene Breakdown, Storyboard, Sound Design, Production Plan).
- `DELETE /project/<id>`
  - Deletes a project and cascades deletions to all sub-documents.

### AI Generators
- `POST /generate-story-analysis`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns Story Synopsis, Theme, Audience insights, Logline, and Tagline.
- `POST /generate-structure`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns 3-Act Narrative structure.
- `POST /generate-screenplay`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns Standard script dialogue page formatted text.
- `POST /generate-characters`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns 3-4 detailed character profiles.
- `POST /generate-scenes`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns Scene location breakdowns.
- `POST /generate-storyboard`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns Storyboard cinematic prompts.
- `POST /generate-sound-design`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns Sound briefs (Ambience, music style, Foley).
- `POST /generate-production-plan`
  - Payload: `{"project_id": "PROJECT_UUID"}`
  - Response: Returns shoot logistics plan.

### Export Center
- `POST /export-project`
  - Payload: `{"project_id": "PROJECT_UUID", "format": "pdf"}` (Formats: `pdf`, `docx`, `txt`)
  - Response: Streams a binary file download.
