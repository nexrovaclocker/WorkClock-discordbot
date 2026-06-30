import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase
from utils import require_founder, log_event

class BlockerModal(discord.ui.Modal, title="Report a Blocker"):
    description = discord.ui.TextInput(label="What is blocking you?", style=discord.TextStyle.paragraph)
    task_id = discord.ui.TextInput(label="Related Task ID (Optional)", required=False)

    def __init__(self, bot, blocking_person: discord.Member = None):
        super().__init__()
        self.bot = bot
        self.blocking_person = blocking_person

    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "reporter_id": str(interaction.user.id),
            "description": str(self.description),
            "task_id": str(self.task_id).strip() if self.task_id.value else None,
            "blocking_person_id": str(self.blocking_person.id) if self.blocking_person else None
        }
        
        # Verify task if provided
        if data["task_id"]:
            res = supabase.table("tasks").select("id").eq("id", data["task_id"]).execute()
            if not res.data:
                await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
                return
                
        res = supabase.table("blockers").insert(data).execute()
        if not res.data:
            await interaction.response.send_message("❌ Failed to report blocker.", ephemeral=True)
            return
            
        blocker_id = res.data[0]["id"]
        
        # If task linked, update task status
        if data["task_id"]:
            supabase.table("tasks").update({"status": "blocked"}).eq("id", data["task_id"]).execute()
            
        log_event("blocker_open", str(interaction.user.id), f"Blocked by {data['description'][:50]}", task_id=data["task_id"])
            
        await interaction.response.send_message(f"✅ Blocker reported. ID: `{blocker_id}`", ephemeral=False)
        
        # DM the blocking person if applicable
        if self.blocking_person:
            try:
                await self.blocking_person.send(f"⚠️ **{interaction.user.display_name}** is blocked by you!\n\n**Reason:** {data['description']}\n**Blocker ID:** `{blocker_id}`")
            except discord.Forbidden:
                pass # They have DMs disabled

class BlockerResolveModal(discord.ui.Modal, title="Resolve Blocker"):
    resolution_note = discord.ui.TextInput(label="How was it resolved?", style=discord.TextStyle.paragraph)

    def __init__(self, blocker):
        super().__init__()
        self.blocker = blocker

    async def on_submit(self, interaction: discord.Interaction):
        now_utc = datetime.now(timezone.utc)
        created_at = datetime.fromisoformat(self.blocker["created_at"])
        hours_open = (now_utc - created_at).total_seconds() / 3600.0
        
        supabase.table("blockers").update({
            "status": "resolved",
            "resolved_at": now_utc.isoformat(),
            "resolved_by": str(interaction.user.id),
            "resolution_note": str(self.resolution_note),
            "hours_open": hours_open
        }).eq("id", self.blocker["id"]).execute()
        
        # If tied to a task, reset task to in_progress or todo
        if self.blocker.get("task_id"):
            # Check if task has other open blockers
            other_blockers = supabase.table("blockers").select("id").eq("task_id", self.blocker["task_id"]).eq("status", "open").execute()
            if not other_blockers.data:
                # No other blockers, revert to in_progress
                supabase.table("tasks").update({"status": "in_progress"}).eq("id", self.blocker["task_id"]).execute()
        
        log_event("blocker_resolve", str(interaction.user.id), f"Resolved blocker after {hours_open:.1f}h: {self.resolution_note}", task_id=self.blocker.get("task_id"))
        
        await interaction.response.send_message(f"✅ Blocker resolved after {hours_open:.1f} hours.", ephemeral=False)

class Blockers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="blocker", description="Report that you are blocked")
    @app_commands.describe(blocking_person="Is a specific person blocking you?")
    async def blocker(self, interaction: discord.Interaction, blocking_person: discord.Member = None):
        await interaction.response.send_modal(BlockerModal(self.bot, blocking_person))

    @app_commands.command(name="blocker-resolve", description="Resolve an open blocker")
    async def blocker_resolve(self, interaction: discord.Interaction, blocker_id: str):
        res = supabase.table("blockers").select("*").eq("id", blocker_id).execute()
        if not res.data:
            await interaction.response.send_message("❌ Blocker not found.", ephemeral=True)
            return
            
        blocker = res.data[0]
        if blocker["status"] != "open":
            await interaction.response.send_message("❌ This blocker is already resolved.", ephemeral=True)
            return
            
        await interaction.response.send_modal(BlockerResolveModal(blocker))

    @app_commands.command(name="blockers-open", description="View all currently open blockers")
    async def blockers_open(self, interaction: discord.Interaction):
        await interaction.response.defer()
        res = supabase.table("blockers").select("*").eq("status", "open").execute()
        if not res.data:
            await interaction.followup.send("🎉 No open blockers!")
            return
            
        embed = discord.Embed(title="🚧 Open Blockers", color=0xE74C3C)
        for b in res.data:
            val = f"**Reporter:** <@{b['reporter_id']}>\n"
            if b.get("blocking_person_id"):
                val += f"**Blocking Person:** <@{b['blocking_person_id']}>\n"
            val += f"**Issue:** {b['description']}\n"
            val += f"**ID:** `{b['id'][:8]}`"
            embed.add_field(name=f"Blocker {b['id'][:4]}", value=val, inline=False)
            
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="blockers-mine", description="View blockers you reported")
    async def blockers_mine(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        res = supabase.table("blockers").select("*").eq("reporter_id", str(interaction.user.id)).eq("status", "open").execute()
        if not res.data:
            await interaction.followup.send("You have no open blockers.", ephemeral=True)
            return
            
        embed = discord.Embed(title="🚧 My Open Blockers", color=0xE74C3C)
        for b in res.data:
            val = f"**Issue:** {b['description']}\n**ID:** `{b['id']}`"
            embed.add_field(name=f"Blocker", value=val, inline=False)
            
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Blockers(bot))
