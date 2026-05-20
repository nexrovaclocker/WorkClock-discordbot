# ⏱️ WorkClock — Discord Work Time Tracker Bot

WorkClock is a feature-rich, zero-friction Discord bot built with **Python (discord.py)** that allows team members to clock in and out of work directly from Discord. All session data is stored in a **PostgreSQL (Supabase)** database.

It is designed for small-to-medium teams, startups, or intern programs looking for a lightweight time tracker without leaving their Discord server.

---

## ✨ Core Features

* **⏱️ Clock In / Out**: `/clockin` to start work, `/clockout` to end it. Supports an optional `work_done` parameter on clock-out. Calculates total elapsed minutes automatically.
* **✏️ Edit Session**: `/editlast` allows you to edit the clock-in or clock-out times of your last completed session.
* **🟢 Session Status**: `/status` shows whether you are currently clocked in, when you started, and your active elapsed time.
* **📊 Personal Summaries**:
  * `/mysummary`: Lists today's active and completed sessions and total hours worked.
  * `/weeklysummary [@user]`: Generates a day-by-day 7-day breakdown of hours worked.
* **👥 Team Reports**: `/teamreport [date]` displays a beautifully formatted monospaced table of all member work sessions on any specific date (available to everyone in the server).
* **🏆 Leaderboard**: `/leaderboard` ranks the top contributors by total hours worked in the last 7 days.
* **🌐 Embedded Keep-Awake Web Server**: Fully compatible with Render's free tier. Contains an embedded `aiohttp` server to prevent the instance from sleeping.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Bot framework** | `discord.py` v2.x (Slash Commands via `app_commands`) |
| **Language** | Python 3.11+ |
| **Database** | PostgreSQL (hosted on Supabase) |
| **DB Client** | `asyncpg` (Asynchronous connection pooling) |
| **Environment Config** | `python-dotenv` |

---

## 🚀 Setup & Installation

### 1. Database Setup
Log into your **Supabase Console** (or any Postgres instance) and run the following in the **SQL Editor** to create the session table:

```sql
CREATE TABLE work_sessions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    clock_in_time TIMESTAMPTZ NOT NULL,
    clock_out_time TIMESTAMPTZ,
    duration_minutes NUMERIC(8, 2),
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_work_sessions_user_date ON work_sessions(user_id, date);
CREATE INDEX idx_work_sessions_guild_date ON work_sessions(guild_id, date);
```

### 2. Local Setup
1. Clone this repository to your local machine.
2. Initialize and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the `.env.template` file to a new file named `.env`:
   ```bash
   cp .env.template .env
   ```
5. Open `.env` and fill in your credentials:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   SUPABASE_DB_URL=postgresql://user:password@hostname:5432/dbname
   TIMEZONE=Asia/Kolkata
   ```
   > ⚠️ **Note**: If your database password contains special characters (like `@`), they **must** be URL-encoded (e.g. `@` becomes `%40`).

### 3. Running Locally
Run the entrypoint script:
```bash
python bot.py
```

---

## ☁️ Deploying to Render (Free Tier)

WorkClock comes equipped with a keep-awake web server inside `bot.py` designed to keep the service running 24/7 on **Render's free tier**:

1. Create a new **Web Service** on Render and connect your GitHub repository.
2. Configure settings:
   * **Language**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python bot.py`
3. Add the following **Environment Variables** on Render:
   * `DISCORD_TOKEN`
   * `SUPABASE_DB_URL`
   * `TIMEZONE` (e.g. `Asia/Kolkata`)
   * `PORT`: `8080` (Render binds to this dynamically)
4. Go to a free ping service like **[UptimeRobot](https://uptimerobot.com/)** or **[Cron-Job.org](https://cron-job.org/)** and configure it to send an HTTP GET request to your Render app URL (`https://your-app-name.onrender.com/`) every 5 to 10 minutes. This will hit the embedded pinger in your bot, ensuring it never goes to sleep!
