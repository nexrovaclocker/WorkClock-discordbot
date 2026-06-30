from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
import discord

from config import supabase, config
from utils import IST_OFFSET
from ai_engine import jarvis_ai

async def check_standups(bot):
    now_ist = datetime.now(timezone.utc) + IST_OFFSET
    today_date = now_ist.strftime("%Y-%m-%d")
    
    members_res = supabase.table("team_members").select("discord_user_id, display_name").eq("is_active", True).execute()
    if not members_res.data:
        return
        
    standups_res = supabase.table("standups").select("user_id").eq("date", today_date).execute()
    submitted_ids = [s["user_id"] for s in standups_res.data] if standups_res.data else []
    
    for member in members_res.data:
        uid = member["discord_user_id"]
        if uid not in submitted_ids:
            try:
                user = await bot.fetch_user(int(uid))
                if user:
                    await user.send(f"Hey {member['display_name']}! Don't forget to submit your `/standup` for today in the server.")
            except Exception as e:
                print(f"Failed to DM {member['display_name']}: {e}")

async def run_morning_briefing(bot):
    briefing_text = await jarvis_ai.morning_briefing()
    for uid in config.MORNING_BRIEFING_USER_IDS:
        try:
            user = await bot.fetch_user(int(uid))
            if user:
                await user.send(f"**☀️ Morning Briefing**\n\n{briefing_text}")
        except Exception as e:
            print(f"Failed to DM morning briefing to {uid}: {e}")

async def run_weekly_narrative(bot):
    narrative_text = await jarvis_ai.weekly_narrative()
    channel = bot.get_channel(config.OPS_BRAIN_CHANNEL_ID)
    if channel:
        await channel.send(f"**🗓️ Friday Weekly Wrap-Up**\n\n{narrative_text}")

async def run_weekly_snapshot(bot):
    print("Running weekly context snapshot...")
    await jarvis_ai.generate_weekly_snapshot()

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler()
    
    # UTC 4:30 AM is IST 10:00 AM
    scheduler.add_job(
        check_standups,
        CronTrigger(day_of_week='mon-fri', hour=4, minute=30, timezone=timezone.utc),
        args=[bot]
    )
    
    # UTC 3:30 AM is IST 9:00 AM
    scheduler.add_job(
        run_morning_briefing,
        CronTrigger(day_of_week='mon-fri', hour=3, minute=30, timezone=timezone.utc),
        args=[bot]
    )
    
    # Friday 6:00 PM IST is Friday 12:30 PM UTC
    scheduler.add_job(
        run_weekly_narrative,
        CronTrigger(day_of_week='fri', hour=12, minute=30, timezone=timezone.utc),
        args=[bot]
    )
    
    # Sunday Midnight IST is Saturday 6:30 PM UTC
    scheduler.add_job(
        run_weekly_snapshot,
        CronTrigger(day_of_week='sat', hour=18, minute=30, timezone=timezone.utc),
        args=[bot]
    )
    
    scheduler.start()
