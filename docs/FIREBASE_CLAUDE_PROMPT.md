# Firebase Migration Prompt for Claude Code

Please implement the following changes to migrate the project to **Firebase Blaze Plan** (Cloud Run or Cloud Functions) with **Firestore** for session persistence.

## 1. Update `requirements.txt`
Add the following dependencies for Firebase integration:
```text
google-cloud-firestore==2.19.0
firebase-admin==6.5.0
asgiref==3.8.1
```

## 2. Modify `main.py` (Firestore Session Persistence)
Replace the in-memory `_sessions` dictionary logic with Firestore to handle the stateless nature of Firebase Functions/Cloud Run.

### Initialization & Firestore Helpers
Replace the `_sessions = {}` line with:
```python
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timezone

# Initialize Firebase (it automatically uses environment credentials in Cloud Run/Functions)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def _get_session_from_db(session_id: str) -> Optional[requests.Session]:
    """Retrieve session from Firestore and reconstruct requests.Session."""
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    sess = _make_session()
    # Reconstruct cookies from the stored dictionary
    sess.cookies.update(data.get("cookies", {}))
    return sess

def _save_session_to_db(session_id: str, sess: requests.Session):
    """Save session cookies to Firestore."""
    doc_ref = db.collection("sessions").document(session_id)
    doc_ref.set({
        "cookies": sess.cookies.get_dict(),
        "last_active": firestore.SERVER_TIMESTAMP
    })
```

### Update Endpoint Logic
- **`POST /api/login`**: Instead of `_sessions[session_id] = sess`, call `_save_session_to_db(session_id, sess)`.
- **`GET /api/download`**: Instead of `_sessions.get(session_id)`, call `_get_session_from_db(session_id)`.
- **`GET /api/debug-page`**: Same as download, use `_get_session_from_db(session_id)`.

## 3. Create Firebase Configuration Files

### `firebase.json`
```json
{
  "hosting": {
    "public": "public_placeholder",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "run": {
          "serviceId": "downloader-api",
          "region": "us-central1"
        }
      }
    ]
  }
}
```

### `firestore.rules`
```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /sessions/{sessionId} {
      allow read, write: if false; // Only server-side access
    }
  }
}
```

## 4. Execution Plan for Claude Code
1.  **Modify `main.py`**:
    - Add Firestore imports and initialization.
    - Replace the global `_sessions` dict with the helper functions provided above.
    - Update all routes that access sessions to use the new Firestore helpers.
2.  **Update `requirements.txt`**: Add the 3 libraries mentioned in section 1.
3.  **Create Config Files**: Create `firebase.json` and `firestore.rules` in the root directory.
4.  **Verification**: Ensure all instances of `_sessions` are replaced by Firestore logic.

---

### Deployment Commands (For Reference)
Once Claude Code finishes the modifications, I can run:
1. `firebase login`
2. `firebase init` (Select Firestore and Hosting)
3. `gcloud builds submit --tag gcr.io/PROJECT_ID/downloader-api`
4. `gcloud run deploy downloader-api --image gcr.io/PROJECT_ID/downloader-api --platform managed --allow-unauthenticated`
5. `firebase deploy --only hosting`
