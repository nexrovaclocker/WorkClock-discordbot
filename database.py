import pytz
from datetime import datetime, timedelta

async def get_open_session(pool, user_id: str, guild_id: str):
    """
    Checks if a user has an active clocked-in session (where clock_out_time is null).
    """
    query = """
        SELECT id, user_id, username, guild_id, clock_in_time, clock_out_time, duration_minutes, date
        FROM work_sessions
        WHERE user_id = $1 AND guild_id = $2 AND clock_out_time IS NULL
        LIMIT 1;
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, user_id, guild_id)

async def create_session(pool, user_id: str, username: str, guild_id: str, tz_name: str):
    """
    Clocks the user in by inserting a new session record.
    """
    tz = pytz.timezone(tz_name)
    now_utc = datetime.now(pytz.utc)
    local_now = now_utc.astimezone(tz)
    local_date = local_now.date()
    
    query = """
        INSERT INTO work_sessions (user_id, username, guild_id, clock_in_time, date)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *;
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, user_id, username, guild_id, now_utc, local_date)

async def close_session(pool, session_id: int, clock_in_time: datetime):
    """
    Clocks the user out, computing the duration and updating the session record.
    """
    now_utc = datetime.now(pytz.utc)
    # Ensure clock_in_time is timezone aware (asyncpg returns tz-aware datetimes)
    if clock_in_time.tzinfo is None:
        clock_in_time = clock_in_time.replace(tzinfo=pytz.utc)
        
    duration = now_utc - clock_in_time
    duration_minutes = round(duration.total_seconds() / 60.0, 2)
    
    query = """
        UPDATE work_sessions
        SET clock_out_time = $1, duration_minutes = $2
        WHERE id = $3
        RETURNING *;
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, now_utc, duration_minutes, session_id)

async def get_user_today_summary(pool, user_id: str, guild_id: str, tz_name: str):
    """
    Retrieves all work sessions for a specific user on today's local date.
    """
    tz = pytz.timezone(tz_name)
    today = datetime.now(tz).date()
    
    query = """
        SELECT id, clock_in_time, clock_out_time, duration_minutes, date
        FROM work_sessions
        WHERE user_id = $1 AND guild_id = $2 AND date = $3
        ORDER BY clock_in_time ASC;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, user_id, guild_id, today)

async def get_user_weekly_summary(pool, user_id: str, guild_id: str, tz_name: str):
    """
    Retrieves all work sessions for a user in the last 7 days.
    """
    tz = pytz.timezone(tz_name)
    today = datetime.now(tz).date()
    start_date = today - timedelta(days=6)
    
    query = """
        SELECT id, clock_in_time, clock_out_time, duration_minutes, date
        FROM work_sessions
        WHERE user_id = $1 AND guild_id = $2 AND date >= $3
        ORDER BY date ASC, clock_in_time ASC;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, user_id, guild_id, start_date)

async def get_team_report(pool, guild_id: str, target_date):
    """
    Retrieves all sessions (active or completed) for the entire guild on a given date.
    """
    query = """
        SELECT username, clock_in_time, clock_out_time, duration_minutes
        FROM work_sessions
        WHERE guild_id = $1 AND date = $2
        ORDER BY username ASC, clock_in_time ASC;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, guild_id, target_date)

async def get_weekly_leaderboard(pool, guild_id: str, tz_name: str):
    """
    Aggregates the total hours worked per user in the last 7 days.
    """
    tz = pytz.timezone(tz_name)
    today = datetime.now(tz).date()
    start_date = today - timedelta(days=6)
    
    query = """
        SELECT user_id, username, SUM(duration_minutes) as total_minutes
        FROM work_sessions
        WHERE guild_id = $1 AND date >= $2 AND clock_out_time IS NOT NULL
        GROUP BY user_id, username
        ORDER BY total_minutes DESC;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, guild_id, start_date)

async def get_last_completed_session(pool, user_id: str, guild_id: str):
    """
    Retrieves the most recent completed work session for a user.
    """
    query = """
        SELECT id, clock_in_time, clock_out_time, duration_minutes, date
        FROM work_sessions
        WHERE user_id = $1 AND guild_id = $2 AND clock_out_time IS NOT NULL
        ORDER BY clock_out_time DESC
        LIMIT 1;
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, user_id, guild_id)

async def update_session_times(pool, session_id: int, new_in: datetime, new_out: datetime, duration_minutes: float):
    """
    Updates the timings and duration of a specific session.
    """
    query = """
        UPDATE work_sessions
        SET clock_in_time = $1, clock_out_time = $2, duration_minutes = $3
        WHERE id = $4
        RETURNING *;
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, new_in, new_out, duration_minutes, session_id)

async def get_all_open_sessions(pool, guild_id: str):
    """
    Retrieves all active (clocked-in) sessions for a given guild.
    """
    query = """
        SELECT user_id, username, clock_in_time, date
        FROM work_sessions
        WHERE guild_id = $1 AND clock_out_time IS NULL
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, guild_id)

