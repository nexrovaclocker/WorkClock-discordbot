import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase, config
from utils import to_ist, format_duration, get_month_key, log_event
from ai_engine import jarvis_ai

class WorkDescriptionModal(discord.ui.Modal, title="Work Session Summary"):
    description = discord.ui.TextInput(
        label="What did you work on?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe your tasks, progress, and any blockers...",
        required=True,
        max_length=1000
    )

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        username = interaction.user.display_name

        active = supabase.table("active_sessions").select("*").eq("user_id", user_id).execute()
        if not active.data:
            await interaction.response.send_message(
                "⚠️ Could not find your active session. Please try again.",
                ephemeral=True
            )
            return

        session = active.data[0]
        clock_in_utc = datetime.fromisoformat(session["clock_in"])
        clock_out_utc = datetime.now(timezone.utc)
        total_seconds = int((clock_out_utc - clock_in_utc).total_seconds())
        readable = format_duration(total_seconds)
        month_key = get_month_key(clock_in_utc)

        clock_in_ist = to_ist(clock_in_utc)
        clock_out_ist = to_ist(clock_out_utc)

        supabase.table("completed_sessions").insert({
            "user_id": user_id,
            "username": username,
            "clock_in": clock_in_utc.isoformat(),
            "clock_out": clock_out_utc.isoformat(),
            "duration_seconds": total_seconds,
            "description": str(self.description),
            "month_key": month_key
        }).execute()

        supabase.table("active_sessions").delete().eq("user_id", user_id).execute()
        
        desc_snippet = str(self.description)[:80] + ("..." if len(str(self.description)) > 80 else "")
        log_event("session_end", user_id, f"{name} worked {format_duration(duration)}: {desc_snippet}")
        
        is_struggling, reason = await jarvis_ai.is_quietly_struggling(str(self.description))
        if is_struggling:
            ops_channel = self.bot.get_channel(config.OPS_BRAIN_CHANNEL_ID)
            if ops_channel:
                await ops_channel.send(f"⚠️ **Potential Struggle Detected:** {name} might be stuck.\n*AI Note:* {reason}")

        channel = self.bot.get_channel(config.STATUS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🔴 Clocked Out",
                description=f"**{username}** has ended their work session.",
                color=0xFF1744,
                timestamp=clock_out_utc
            )
            embed.add_field(name="⏱️ Duration", value=readable, inline=True)
            embed.add_field(
                name="🕐 Session (IST)",
                value=f"{clock_in_ist.strftime('%H:%M:%S')} → {clock_out_ist.strftime('%H:%M:%S')}",
                inline=True
            )
            embed.add_field(name="📝 Work Summary", value=str(self.description), inline=False)
            await channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ Clocked out! You worked for **{readable}**. Great work!",
            ephemeral=True
        )


class Tracking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clockin", description="Clock in to start your work session")
    async def clockin(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        username = interaction.user.display_name

        existing = supabase.table("active_sessions").select("user_id").eq("user_id", user_id).execute()
        if existing.data:
            await interaction.followup.send(
                "⚠️ You are already clocked in! Use `/clockout` to end your session first.",
                ephemeral=True
            )
            return

        now_utc = datetime.now(timezone.utc)
        now_display = to_ist(now_utc)

        supabase.table("active_sessions").insert({
            "user_id": user_id,
            "username": username,
            "clock_in": now_utc.isoformat()
        }).execute()

        channel = self.bot.get_channel(config.STATUS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🟢 Clocked In",
                description=f"**{username}** has started their work session.",
                color=0x00C853,
                timestamp=now_utc
            )
            embed.add_field(
                name="🕐 Clock-in Time",
                value=f"`{now_display.strftime('%Y-%m-%d %H:%M:%S')} IST`",
                inline=False
            )
            embed.set_footer(text=f"User ID: {user_id}")
            await channel.send(embed=embed)

        await interaction.followup.send(
            f"✅ You have been clocked in at `{now_display.strftime('%Y-%m-%d %H:%M:%S')} IST`. Good luck!",
            ephemeral=True
        )

    @app_commands.command(name="clockout", description="Clock out and submit your work summary")
    async def clockout(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        existing = supabase.table("active_sessions").select("user_id").eq("user_id", user_id).execute()
        if not existing.data:
            await interaction.response.send_message(
                "⚠️ You are not clocked in! Use `/clockin` to start a session.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(WorkDescriptionModal(self.bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Tracking(bot))
