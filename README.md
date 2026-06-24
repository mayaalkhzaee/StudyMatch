# StudyMatch

A study group finder built for EECE480 — Internet Computing. Students can post and browse in-person or online study sessions, join or leave them, get recommendations, and track their activity through a personal dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | MongoDB (local) via Motor async driver |
| Auth | JWT (`PyJWT`), password hashing via `pwdlib` |
| Frontend | Vanilla JS, Bootstrap 5.3, Chart.js, FullCalendar 6 |
| Config | `python-dotenv` |

No frontend framework — HTML files are served directly from the browser.

---

## Project Structure

```
StudyMatch/
├── backend/
│   ├── main.py          # FastAPI app, router registration, CORS
│   ├── database.py      # Motor AsyncMongoClient + lifespan
│   ├── auth.py          # JWT helpers, password hashing, /auth router
│   ├── sessions.py      # /sessions router
│   ├── users.py         # /users router
│   └── stats.py         # /stats router
├── frontend/
│   ├── js/
│   │   ├── auth.js      # localStorage helpers (getToken, authHeaders, logout, etc.)
│   │   └── navbar.js    # Toggles guest vs logged-in navbar state + theme toggle
│   ├── index.html            # Landing page
│   ├── login.html            # Login form
│   ├── register.html         # Registration form
│   ├── sessions.html         # Browse all sessions (card + calendar view)
│   ├── post-session.html     # Create a new session
│   ├── dashboard.html        # Your hosted + joined sessions + recommendations
│   ├── profile.html          # Edit username/email, delete account
│   ├── stats.html            # App-wide stats (Chart.js charts)
│   └── navbar_template.html  # Reference navbar snippet for copy-pasting
├── .env                 # Not committed — see setup below
├── requirements.txt
├── API_contract.md
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

Make sure MongoDB is running on port 27017. If it's installed as a service it might already be running. Otherwise:

```bash
mongod
```

### 5. Run the backend

From inside `backend/`:

```bash
uvicorn main:app --reload
```

API is live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 6. Open the frontend

Open any `.html` file in `frontend/` directly in your browser. No build step needed.

---

## API Overview

Full details are in [API_contract.md](API_contract.md). Quick reference:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Login, get JWT |
| GET | `/sessions` | No | All sessions |
| GET | `/sessions/recommended` | Yes | Recommended for you |
| GET | `/sessions/{id}` | No | Single session |
| POST | `/sessions` | Yes | Post a session |
| PUT | `/sessions/{id}` | Yes | Edit your session |
| DELETE | `/sessions/{id}` | Yes | Delete your session |
| POST | `/sessions/{id}/join` | Yes | Join a session |
| POST | `/sessions/{id}/leave` | Yes | Leave a session |
| GET | `/users/me` | Yes | Your profile |
| PUT | `/users/me` | Yes | Update username/email |
| DELETE | `/users/me` | Yes | Delete account |
| GET | `/users/me/sessions` | Yes | Sessions you host |
| GET | `/users/me/joined` | Yes | Sessions you joined |
| GET | `/stats` | No | App-wide stats |

Protected routes require `Authorization: Bearer <token>` in the request header.

---

## Auth Flow

1. Register at `/auth/register` → password is argon2-hashed and stored in MongoDB.
2. Login at `/auth/login` → get a JWT token back. You can log in with either email or username.
3. Frontend stores `token` and `username` in `localStorage`.
4. Every protected fetch attaches the token:
   ```js
   fetch(BASE_URL + '/sessions', {
     headers: { 'Authorization': 'Bearer ' + getToken() }
   })
   ```
5. Backend decodes the JWT with `PyJWT`, looks up the user, returns 401 if invalid.
6. Logout clears `localStorage` and redirects to `login.html`.

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
  "host": "string",
  "host_id": "user id",
  "type": "online | in-person",
  "location": "string (room name or meeting link)",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "capacity": 5,
  "enrolled_count": 2,
  "enrolled_users": ["user id", "..."]
}
```

Both `_id` fields are UUID strings generated by the backend, not MongoDB ObjectIds.

---

## Course Info

- Course: EECE480 — Internet Computing
- Semester: Summer 2026
