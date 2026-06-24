# API Contract — StudyMatch

This is the shared reference for frontend ↔ backend. Don't change endpoint names, field names, or response shapes without updating this file.

**Base URL:** `http://localhost:8000`

All protected routes need this header:
```
Authorization: Bearer <token>
```

Errors always come back as:
```json
{ "detail": "Error message here" }
```

Status codes: `200` OK, `201` Created, `400` Bad request, `401` Unauthorized, `403` Forbidden, `404` Not found.

---

## Auth

### POST `/auth/register`
No auth required.

Request:
```json
{
  "username": "maya",
  "email": "maya@uni.edu",
  "password": "secret123"
}
```

Response `201`:
```json
{
  "id": "abc123",
  "username": "maya",
  "email": "maya@uni.edu"
}
```

---

### POST `/auth/login`
No auth required. The `email` field accepts either an email address or a username.

Request:
```json
{
  "email": "maya@uni.edu",
  "password": "secret123"
}
```

Response `200`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Sessions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/sessions` | No | All sessions |
| GET | `/sessions/recommended` | Yes | Recommended sessions for current user |
| GET | `/sessions/{id}` | No | Single session |
| POST | `/sessions` | Yes | Create a session |
| PUT | `/sessions/{id}` | Yes | Edit your session |
| DELETE | `/sessions/{id}` | Yes | Delete your session |
| POST | `/sessions/{id}/join` | Yes | Join a session |
| POST | `/sessions/{id}/leave` | Yes | Leave a session |

### Session object (returned by all session endpoints)
```json
{
  "_id": "sess456",
  "course": "EECE480",
  "host": "maya",
  "host_id": "abc123",
  "type": "online",
  "location": "https://zoom.us/j/123",
  "date": "2026-06-15",
  "time": "15:00",
  "capacity": 5,
  "enrolled_count": 2,
  "enrolled_users": ["abc123", "xyz789"]
}
```

`type` is always `"online"` or `"in-person"`. `location` is a room/address for in-person or a meeting link for online.

---

### GET `/sessions`
Returns all sessions as an array.

---

### GET `/sessions/recommended`
Auth required. Returns sessions in courses the user has already joined, excluding sessions they host or are already in.

Returns an array of session objects. Returns `[]` if the user hasn't joined anything yet.

---

### GET `/sessions/{id}`
Returns a single session object. `404` if not found.

---

### POST `/sessions`
Request:
```json
{
  "course": "EECE480",
  "type": "online",
  "location": "https://zoom.us/j/123",
  "date": "2026-06-15",
  "time": "15:00",
  "capacity": 5
}
```

Response `201` — the created session object. `400` if the date is in the past.

---

### PUT `/sessions/{id}`
Same body as POST (all fields optional — only send what changed). Only the session host can edit.

Response `200` — the updated session object. `403` if not the host.

---

### DELETE `/sessions/{id}`
No body. Only the host can delete.

Response `200`:
```json
{ "message": "Session deleted successfully" }
```
`403` if not the host.

---

### POST `/sessions/{id}/join`
No body.

Response `200`:
```json
{
  "message": "Successfully joined session",
  "enrolled_count": 3
}
```

`400` if already joined or session is full.

---

### POST `/sessions/{id}/leave`
No body.

Response `200`:
```json
{
  "message": "Successfully left session",
  "enrolled_count": 2
}
```

`400` if not enrolled.

---

## Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | Yes | Current user's profile |
| PUT | `/users/me` | Yes | Update username or email |
| DELETE | `/users/me` | Yes | Delete account |
| GET | `/users/me/sessions` | Yes | Sessions the user hosts |
| GET | `/users/me/joined` | Yes | Sessions the user joined |

### GET `/users/me`
Response `200`:
```json
{
  "id": "abc123",
  "username": "maya",
  "email": "maya@uni.edu"
}
```

---

### PUT `/users/me`
Send only the fields you want to change.

Request:
```json
{
  "username": "maya2",
  "email": "newemail@uni.edu"
}
```

Response `200` — updated user object. `400` if the new username or email is already taken. Updating the username also updates the `host` field on all sessions that user hosts.

---

### DELETE `/users/me`
No body. Deletes the account and cascades:
- Removes the user from any sessions they were enrolled in (decrements `enrolled_count`)
- Deletes all sessions they hosted

Response `200`:
```json
{ "message": "Account deleted successfully" }
```

---

### GET `/users/me/sessions`
Response `200` — array of session objects hosted by the current user.

---

### GET `/users/me/joined`
Response `200` — array of session objects the current user is enrolled in.

---

## Stats

### GET `/stats`
No auth required.

Response `200`:
```json
{
  "top_courses": [
    { "course": "EECE480", "session_count": 8 },
    { "course": "MATH201", "session_count": 5 }
  ],
  "sessions_per_week": [
    { "week": "2026-06-15", "count": 5 },
    { "week": "2026-06-16", "count": 3 }
  ],
  "top_participants": [
    { "username": "maya", "joined_count": 6 },
    { "username": "ahmed", "joined_count": 4 }
  ]
}
```

`top_courses` and `top_participants` are capped at 5. `sessions_per_week` is grouped by date and sorted chronologically.

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
  "location": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "capacity": 5,
  "enrolled_count": 2,
  "enrolled_users": ["user id", "..."]
}
```

Both `_id` fields are UUID strings generated by the backend, not MongoDB ObjectIds.

---

*Last updated: June 2026*
