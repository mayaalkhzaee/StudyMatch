from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
async def get_stats(request: Request):
    db = request.app.database

    sessions_cursor = db["sessions"].find()
    sessions = [s async for s in sessions_cursor]

    users_cursor = db["users"].find()
    users = [u async for u in users_cursor]

    course_counts = {}
    date_counts = {}

    for session in sessions:
        course = session.get("course")
        if course:
            course_counts[course] = course_counts.get(course, 0) + 1

        date = session.get("date")
        if date:
            date_counts[date] = date_counts.get(date, 0) + 1

    sorted_courses = sorted(
        course_counts.items(), key=lambda item: item[1], reverse=True
    )
    top_courses = [
        {"course": k, "session_count": v}
        for k, v in sorted_courses[:5]
    ]

    sorted_dates = sorted(date_counts.items(), key=lambda item: item[0])
    sessions_per_week = [
        {"week": k, "count": v} for k, v in sorted_dates
    ]

    user_counts = []
    for user in users:
        username = user.get("username")
        joined_count = len(user.get("joined_session_ids", []))
        user_counts.append((username, joined_count))

    sorted_users = sorted(
        user_counts, key=lambda item: item[1], reverse=True
    )
    top_participants = [
        {"username": k, "joined_count": v}
        for k, v in sorted_users[:5]
    ]

    return {
        "top_courses": top_courses,
        "sessions_per_week": sessions_per_week,
        "top_participants": top_participants
    }
