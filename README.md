# WorkTracker Bot (Jarvis AI)

A robust Discord bot for managing tasks, blockers, daily standups, and providing AI-powered operational intelligence using Azure OpenAI.

## Features
- **Task Management**: Create, assign, claim, and complete tasks.
- **Blocker Tracking**: Report blockers and automatically notify blocking personnel.
- **Daily Operations**: Submits and tracks daily standups, tracks active work sessions.
- **Jarvis AI (Ops-Brain)**: Analyzes work context and answers questions directly in `#ops-brain`.
- **Automated Intelligence**: Posts a daily Morning Briefing and a Friday Weekly Wrap-Up.

## Tech Stack
- **Python 3.10+**
- **discord.py**: Discord API wrapper.
- **Supabase**: Postgres database for state management and context logging.
- **APScheduler**: Background jobs (Cron).
- **OpenAI (AsyncAzureOpenAI)**: The AI Engine behind Jarvis.

## Setup Instructions

1. **Clone the Repository**
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Set up Environment Variables**: Create a `.env` file based on the config.py requirements:
   ```env
   TOKEN=your_discord_bot_token
   STATUS_CHANNEL_ID=12345
   STANDUP_CHANNEL_ID=12345
   OPS_BRAIN_CHANNEL_ID=12345
   FOUNDER_DISCORD_IDS=id1,id2
   MORNING_BRIEFING_USER_IDS=id1,id2
   SUPABASE_URL=your_supabase_url
   SUPABASE_SECRET_KEY=your_supabase_service_role_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_KEY=your_azure_key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```
4. **Database Setup**: Execute `database_schema.sql` in your Supabase SQL Editor to build all tables.
5. **Run the Bot**: `python main.py`

## Architecture Overview
- `main.py`: Entry point, sets up cogs.
- `config.py`: Environment variable validation and Supabase initialization.
- `ai_engine.py`: Contains the `JarvisAI` class which interacts with Azure OpenAI.
- `scheduler.py`: Handles all background cron jobs (Standup reminders, AI briefings).
- `cogs/`: Contains modular Discord slash commands categorized by domain.

## Deployment
This project includes a `Procfile` and a background `health_server.py` to easily deploy to platforms like Render or Heroku.
