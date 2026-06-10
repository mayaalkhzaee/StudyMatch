# StudyMatch — API Contract

> **This is the shared reference for frontend and backend development.**  
> Frontend calls these exact endpoints. Backend implements them exactly as specified.  
> Do not change endpoint names, field names, or response shapes without updating this file and notifying your teammate.

---

## Base URL

```
http://localhost:8000
```

> For production/deployment, replace with the live server URL.

## Authentication Header

All protected routes (marked ✅) require:

```
Authorization: Bearer <token>
```

The token is returned by `/auth/login` and must be stored on the frontend and attached to every protected request.

---

## Error Format

All errors across every endpoint follow this shape:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (e.g. validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (e.g. trying to edit someone else's session) |
| 404 | Not found |

---

## Auth

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/register` | ❌ | Register a new user |
| POST | `/auth/login` | ❌ | Login and receive JWT token |

### POST `/auth/register`

**Request**
```json
{
  "username": "maya",
  "email": "maya@uni.edu",
  "password": "secret123"
}
```

**Response `201`**
```json
{
  "id": "abc123",
  "username": "maya",
  "email": "maya@uni.edu"
}
```

---

### POST `/auth/login`

**Request**
```json
{
  "email": "maya@uni.edu",
  "password": "secret123"
}
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Sessions

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/sessions` | ❌ | Get all sessions |
| GET | `/sessions/{id}` | ❌ | Get a single session |
| POST | `/sessions` | ✅ | Create a new session |
| PUT | `/sessions/{id}` | ✅ | Edit your own session |
| DELETE | `/sessions/{id}` | ✅ | Delete your own session |

### Session Object (returned in all session responses)

```json
{
  "id": "sess456",
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

> `type` is always either `"online"` or `"in-person"`.  
> `location` is a room/address for in-person, or a meeting link for online.

---

### GET `/sessions`

Returns array of all session objects.

**Response `200`**
```json
[
  { ...session object... },
  { ...session object... }
]
```

---

### GET `/sessions/{id}`

**Response `200`** — single session object.  
**Response `404`** if session not found.

---

### POST `/sessions`

**Request**
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

**Response `201`** — the created session object.

---

### PUT `/sessions/{id}`

Same request body as POST. Only the session host can edit.

**Response `200`** — the updated session object.  
**Response `403`** if the current user is not the host.

---

### DELETE `/sessions/{id}`

No request body. Only the session host can delete.

**Response `200`**
```json
{
  "message": "Session deleted successfully"
}
```
**Response `403`** if the current user is not the host.

---

## Enrollments

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/sessions/{id}/join` | ✅ | Join a session |
| POST | `/sessions/{id}/leave` | ✅ | Leave a session |

### POST `/sessions/{id}/join`

No request body.

**Response `200`**
```json
{
  "message": "Successfully joined session",
  "enrolled_count": 3
}
```

**Response `400`** if session is full:
```json
{
  "detail": "Session is full"
}
```

**Response `400`** if already joined:
```json
{
  "detail": "You have already joined this session"
}
```

---

### POST `/sessions/{id}/leave`

No request body.

**Response `200`**
```json
{
  "message": "Successfully left session",
  "enrolled_count": 2
}
```

**Response `400`** if not enrolled:
```json
{
  "detail": "You are not enrolled in this session"
}
```

---

## Users

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/users/me` | ✅ | Get current user profile |
| GET | `/users/me/sessions` | ✅ | Sessions the current user created |
| GET | `/users/me/joined` | ✅ | Sessions the current user joined |

### GET `/users/me`

**Response `200`**
```json
{
  "id": "abc123",
  "username": "maya",
  "email": "maya@uni.edu"
}
```

---

### GET `/users/me/sessions`

**Response `200`** — array of session objects hosted by current user.

---

### GET `/users/me/joined`

**Response `200`** — array of session objects the current user has joined.

---

## Stats

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/stats` | ❌ | Summary data for the statistics dashboard |

### GET `/stats`

**Response `200`**
```json
{
  "top_courses": [
    { "course": "EECE480", "session_count": 8 },
    { "course": "MATH201", "session_count": 5 }
  ],
  "sessions_per_week": [
    { "week": "2026-06-09", "count": 5 },
    { "week": "2026-06-16", "count": 3 }
  ],
  "top_participants": [
    { "username": "maya", "joined_count": 6 },
    { "username": "ahmed", "joined_count": 4 }
  ]
}
```

---

## MongoDB Collections Reference

> For backend use. Defines what gets stored.

### `users`
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "hashed_password": "string",
  "joined_session_ids": ["ObjectId"]
}
```

### `sessions`
```json
{
  "_id": "ObjectId",
  "course": "string",
  "host_id": "ObjectId",
  "type": "online | in-person",
  "location": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "capacity": "int",
  "enrolled_user_ids": ["ObjectId"]
}
```

### `enrollments`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "session_id": "ObjectId",
  "enrolled_at": "ISODate"
}
```

---

*Last updated: June 2026*