# StudyMatch

A study group finder web app built for EECE480 — Internet Computing. Students can post and discover in-person or online study sessions, join or leave them, and track their activity through a personal dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | MongoDB (local) via `pymongo` AsyncMongoClient |
| Auth | JWT (`PyJWT`), password hashing via `pwdlib` |
| Frontend | Vanilla JavaScript, Bootstrap 5, Chart.js |
| Config | `python-dotenv` (`dotenv_values`) |

No frontend framework. HTML files are opened directly in the browser.

---

## Project Structure

```
StudyMatch/
├── backend/
│   ├── routers/              # One APIRouter per resource (sessions, users, stats)
│   ├── models/               # Pydantic models for each resource
│   ├── main.py               # FastAPI app entry point, router registration
│   ├── database.py           # AsyncMongoClient + lifespan context manager
│   └── auth.py               # JWT helpers, password hashing, /auth router
├── frontend/
│   ├── js/
│   │   ├── navbar.js         # Navbar auth state toggle (guest vs logged-in)
│   │   └── auth.js           # Login / register fetch calls, localStorage helpers
│   ├── css/                  # Custom styles (if any)
│   ├── index.html            # Landing page
│   ├── dashboard.html        # User's hosted + joined sessions
│   ├── sessions.html         # Browse all study sessions
│   ├── post-session.html     # Create a new session form
│   ├── register.html         # Registration form
│   ├── login.html            # Login form
│   ├── stats.html            # Stats dashboard (Chart.js charts)
│   └── navbar_template.html  # Copy-paste navbar component (see below)
├── .env                      # Environment variables (not committed)
├── requirements.txt          # Python dependencies
├── API_contract.md           # Shared frontend/backend API reference
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/mayaalkhzaee/StudyMatch.git
cd StudyMatch
```

### 2. Create `.env`

Create a `.env` file in the project root:

```
DB_URI=mongodb://localhost:27017
DB_NAME=studymatch
JWT_SECRET=your_secret_key_here
```

### 3. Install Python dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r ../requirements.txt
```

### 4. Start MongoDB

Make sure MongoDB is running locally on port 27017. If you have it installed as a service it may already be running. Otherwise:

```bash
mongod
```

### 5. Run the backend

From inside the `backend/` folder:

```bash
uvicorn main:app --reload
```

The API is now live at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 6. Open the frontend

Open any `.html` file in `frontend/` directly in your browser. No build step needed.

---

## API Overview

Full details are in [API_contract.md](API_contract.md). Quick reference:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Login, get JWT token |
| GET | `/sessions` | No | List all sessions |
| GET | `/sessions/{id}` | No | Get one session |
| POST | `/sessions` | Yes | Create a session |
| PUT | `/sessions/{id}` | Yes | Edit your session |
| DELETE | `/sessions/{id}` | Yes | Delete your session |
| POST | `/sessions/{id}/join` | Yes | Join a session |
| POST | `/sessions/{id}/leave` | Yes | Leave a session |
| GET | `/users/me` | Yes | Your profile |
| GET | `/users/me/sessions` | Yes | Sessions you host |
| GET | `/users/me/joined` | Yes | Sessions you joined |
| GET | `/stats` | No | App-wide stats |

Protected routes require `Authorization: Bearer <token>` in the request header.

---

## Auth Flow

1. User registers at `/auth/register` → account stored in MongoDB with bcrypt-hashed password.
2. User logs in at `/auth/login` → receives a JWT token.
3. Frontend stores `token` and `username` in `localStorage`.
4. Every protected `fetch()` call attaches the token:
   ```js
   fetch('http://localhost:8000/sessions', {
       headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
   })
   ```
5. Backend decodes the token with `PyJWT`, looks up the user in MongoDB, and returns a 401 if invalid.
6. Logout clears `localStorage` and redirects to `login.html`.

---

## Navbar Component

`frontend/navbar_template.html` is a reference file showing the reusable navbar. To add the navbar to any page, copy three things:

**In `<head>`:**
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
```

**At the top of `<body>`:** copy the `<nav>` block from `navbar_template.html`.

**At the bottom of `<body>`:**
```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="js/navbar.js"></script>
```

`navbar.js` reads `localStorage` on page load and:
- Shows **Login / Register** buttons if no token is found.
- Shows **Hi, [username] + Logout** if a token is found.
- Logout clears `localStorage` and redirects to `login.html`.

---

## MongoDB Collections

### `users`
```json
{
  "_id": "uuid string",
  "username": "string",
  "email": "string",
  "hashed_password": "string",
  "joined_session_ids": ["session id", "..."]
}
```

### `sessions`
```json
{
  "_id": "uuid string",
  "course": "string",
  "host_id": "user id",
  "type": "online | in-person",
  "location": "string (room or link)",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "capacity": 5,
  "enrolled_user_ids": ["user id", "..."]
}
```

---

## Course Info

- Course: EECE480 — Internet Computing
- Semester: Summer 2026
