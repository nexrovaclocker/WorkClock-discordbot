import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase, config
from utils import format_duration, is_admin

class ContextAddModal(discord.ui.Modal, title="Add Manual Context"):
    context_type = discord.ui.TextInput(label="Type (client/decision/risk/general)", default="general")
    content = discord.ui.TextInput(label="Context Details", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        supabase.table("manual_context").insert({
            "added_by": str(interaction.user.id),
            "context_type": str(self.context_type),
            "content": str(self.content)
        }).execute()
        
        from utils import log_event
        log_event("manual_context", str(interaction.user.id), f"[{self.context_type}] {self.content}")
        
        await interaction.response.send_message(f"✅ Manual context added.", ephemeral=True)

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="resetmonth", description="Admin only: archive this month's logs and start fresh")
    async def resetmonth(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not is_admin(str(interaction.user.id)):
            await interaction.followup.send(
                "❌ You do not have permission to run this command.",
                ephemeral=True
            )
            return

        result = supabase.table("completed_sessions").select("*").execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send(
                "There are no completed sessions to archive. The log is already empty.",
                ephemeral=True
            )
            return

        archive_rows = []
        for s in sessions:
            archive_rows.append({
                "user_id": s["user_id"],
                "username": s["username"],
                "clock_in": s["clock_in"],
                "clock_out": s["clock_out"],
                "duration_seconds": s["duration_seconds"],
                "description": s["description"],
                "month_key": s["month_key"]
            })

        supabase.table("archived_sessions").insert(archive_rows).execute()
        supabase.table("completed_sessions").delete().neq("id", 0).execute()

        now_utc = datetime.now(timezone.utc)
        embed = discord.Embed(
            title="🗂️ Month Reset Complete",
            color=0x00C853,
            timestamp=now_utc
        )
        embed.add_field(
            name="Sessions Archived",
            value=f"`{len(sessions)}` session(s) moved to the archive table in Supabase",
            inline=False
        )
        embed.add_field(
            name="Active Sessions",
            value="Anyone currently clocked in has been left untouched.",
            inline=False
        )
        embed.add_field(
            name="Fresh Start",
            value="The live log is now empty and ready for the new month.",
            inline=False
        )
        embed.set_footer(text=f"Reset performed by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="viewlog", description="Admin only: display a summary of the current work log")
    async def viewlog(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not is_admin(str(interaction.user.id)):
            await interaction.followup.send(
                "❌ You do not have permission to run this command.",
                ephemeral=True
            )
            return

        active_result = supabase.table("active_sessions").select("*").execute()
        completed_result = supabase.table("completed_sessions").select("*").execute()
        active_sessions = active_result.data
        completed_sessions = completed_result.data

        user_totals = {}
        for s in completed_sessions:
            uid = s["user_id"]
            if uid not in user_totals:
                user_totals[uid] = {"username": s["username"], "seconds": 0}
            user_totals[uid]["seconds"] += s["duration_seconds"]

        sorted_users = sorted(user_totals.items(), key=lambda x: x[1]["seconds"], reverse=True)
        lines = [f"**{info['username']}** — `{format_duration(info['seconds'])}`" for _, info in sorted_users]

        embed = discord.Embed(
            title="📁 Current Work Log",
            color=0x7C4DFF,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Active Sessions", value=str(len(active_sessions)), inline=True)
        embed.add_field(name="Completed Sessions", value=str(len(completed_sessions)), inline=True)
        embed.add_field(
            name="Totals Per User",
            value="\n".join(lines) if lines else "No data yet.",
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="register", description="Founder/Admin: Register a team member in Jarvis")
    @app_commands.describe(person="The team member", role="Their role (e.g. intern, founder, developer)")
    async def register(self, interaction: discord.Interaction, person: discord.Member, role: str = "intern"):
        await interaction.response.defer(ephemeral=True)
        if not (is_admin(str(interaction.user.id)) or str(interaction.user.id) in config.FOUNDER_IDS):
            await interaction.followup.send("❌ You do not have permission.", ephemeral=True)
            return
            
        supabase.table("team_members").upsert({
            "discord_user_id": str(person.id),
            "username": person.name,
            "display_name": person.display_name,
            "role": role
        }, on_conflict="discord_user_id").execute()
        
        
        await interaction.followup.send(f"✅ Registered **{person.display_name}** as `{role}`.", ephemeral=True)

    @app_commands.command(name="context-add", description="Admin only: Add manual system context")
    async def context_add(self, interaction: discord.Interaction):
        if not is_admin(str(interaction.user.id)):
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return
        await interaction.response.send_modal(ContextAddModal())

    @app_commands.command(name="jarvis-status", description="Admin only: View bot health and database stats")
    async def jarvis_status(self, interaction: discord.Interaction):
        if not is_admin(str(interaction.user.id)):
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            tasks_res = supabase.table("tasks").select("id", count="exact").execute()
            modules_res = supabase.table("modules").select("id", count="exact").execute()
            blockers_res = supabase.table("blockers").select("id", count="exact").execute()
            logs_res = supabase.table("context_log").select("id", count="exact").execute()
            
            t_count = tasks_res.count if hasattr(tasks_res, "count") else len(tasks_res.data or [])
            m_count = modules_res.count if hasattr(modules_res, "count") else len(modules_res.data or [])
            b_count = blockers_res.count if hasattr(blockers_res, "count") else len(blockers_res.data or [])
            l_count = logs_res.count if hasattr(logs_res, "count") else len(logs_res.data or [])
            
            embed = discord.Embed(title="🤖 Jarvis System Health", color=0x3498DB)
            embed.add_field(name="Modules", value=str(m_count))
            embed.add_field(name="Tasks", value=str(t_count))
            embed.add_field(name="Blockers", value=str(b_count))
            embed.add_field(name="Context Logs", value=str(l_count))
            
            from ai_engine import jarvis_ai
            ai_status = "🟢 Connected" if jarvis_ai.client else "🔴 Disconnected"
            embed.add_field(name="Azure OpenAI", value=ai_status, inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error fetching status: {e}")

    @app_commands.command(name="force-clockout-all", description="Admin only: Force clock out everyone currently working")
    async def force_clockout_all(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not is_admin(str(interaction.user.id)):
            await interaction.followup.send("❌ You do not have permission.", ephemeral=True)
            return

        active_res = supabase.table("active_sessions").select("*").execute()
        sessions = active_res.data
        if not sessions:
            await interaction.followup.send("No one is currently clocked in.", ephemeral=True)
            return

        now_utc = datetime.now(timezone.utc)
        completed_rows = []
        clocked_out_names = []
        
        from utils import get_month_key, log_event, format_duration

        for session in sessions:
            user_id = session["user_id"]
            username = session["username"]
            clock_in_utc = datetime.fromisoformat(session["clock_in"])
            if clock_in_utc.tzinfo is None:
                clock_in_utc = clock_in_utc.replace(tzinfo=timezone.utc)
            total_seconds = int((now_utc - clock_in_utc).total_seconds())
            
            completed_rows.append({
                "user_id": user_id,
                "username": username,
                "clock_in": session["clock_in"],
                "clock_out": now_utc.isoformat(),
                "duration_seconds": total_seconds,
                "description": "Force clocked out by Admin",
                "month_key": get_month_key(clock_in_utc)
            })
            clocked_out_names.append(username)
            log_event("session_end", user_id, f"Force clocked out. Duration: {format_duration(total_seconds)}")

        if completed_rows:
            supabase.table("completed_sessions").insert(completed_rows).execute()
            for s in sessions:
                supabase.table("active_sessions").delete().eq("user_id", s["user_id"]).execute()

        channel = self.bot.get_channel(config.STATUS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🔴 Mass Clock Out",
                description=f"An admin has force clocked out **{len(sessions)}** user(s).",
                color=0xFF1744,
                timestamp=now_utc
            )
            embed.add_field(name="Affected Users", value=", ".join(clocked_out_names), inline=False)
            await channel.send(embed=embed)

        await interaction.followup.send(f"✅ Force clocked out {len(sessions)} user(s): {', '.join(clocked_out_names)}.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
