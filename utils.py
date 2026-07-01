import discord
from discord import app_commands
import json
from datetime import datetime, timezone, timedelta
from config import config, supabase
from config_manager import bot_config

IST_OFFSET = timedelta(hours=5, minutes=30)

def to_ist(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt + IST_OFFSET

def now_ist():
    return datetime.now(timezone.utc) + IST_OFFSET

def format_duration(total_seconds):
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

def get_month_key(dt=None):
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m")

def is_founder(user_id: str) -> bool:
    return bot_config.is_founder(user_id)

def is_admin(user_id: str) -> bool:
    return bot_config.is_admin(user_id)

def require_founder():
    """Decorator-style check for slash commands."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_founder(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ This command is for founders only.", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def log_event(event_type: str, user_id: str = None, content: str = "", task_id: str = None, module_id: str = None, metadata: dict = None):
    data = {
        "event_type": event_type,
        "user_id": str(user_id) if user_id else None,
        "content": content,
        "task_id": str(task_id) if task_id else None,
        "module_id": str(module_id) if module_id else None,
        "metadata": metadata if metadata else None
    }
    try:
        supabase.table("context_log").insert(data).execute()
    except Exception as e:
        print(f"Error logging event {event_type}: {e}")

