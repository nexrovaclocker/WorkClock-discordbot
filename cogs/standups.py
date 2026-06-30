import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import dateutil.parser

from config import supabase, config
from utils import to_ist, IST_OFFSET, is_admin, log_event

class StandupModal(discord.ui.Modal, title="Daily Standup"):
    yesterday = discord.ui.TextInput(label="What did you work on?", style=discord.TextStyle.paragraph)
    today = discord.ui.TextInput(label="What's your focus today?", style=discord.TextStyle.paragraph)
    blockers = discord.ui.TextInput(label="Any blockers or risks?", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        now_ist = datetime.now(timezone.utc) + IST_OFFSET
        today_date = now_ist.strftime("%Y-%m-%d")
        
        data = {
            "user_id": str(interaction.user.id),
            "date": today_date,
            "yesterday": str(self.yesterday),
            "today": str(self.today),
            "blockers": str(self.blockers) if self.blockers.value else "None"
        }
        
        # Upsert standup
        res = supabase.table("standups").upsert(data, on_conflict="user_id,date").execute()
        
        log_event("standup", str(interaction.user.id), f"Yesterday: {data['yesterday'][:30]}... Today: {data['today'][:30]}... Blockers: {data['blockers'][:30]}...")
        
        await interaction.response.send_message("✅ Standup submitted!", ephemeral=True)
        
        # Post to channel
        channel = self.bot.get_channel(config.STANDUP_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title=f"Standup: {interaction.user.display_name}", color=0xF1C40F)
            embed.add_field(name="Yesterday", value=data["yesterday"], inline=False)
            embed.add_field(name="Today", value=data["today"], inline=False)
            embed.add_field(name="Blockers", value=data["blockers"], inline=False)
            embed.set_footer(text=today_date)
            await channel.send(embed=embed)


class Standups(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="standup", description="Submit your daily standup")
    async def standup(self, interaction: discord.Interaction):
        await interaction.response.send_modal(StandupModal(self.bot))

    @app_commands.command(name="standup-missed", description="Admin only: See who hasn't submitted a standup today")
    async def standup_missed(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not is_admin(str(interaction.user.id)):
            await interaction.followup.send("❌ You do not have permission.")
            return
            
        now_ist = datetime.now(timezone.utc) + IST_OFFSET
        today_date = now_ist.strftime("%Y-%m-%d")
        
        # Get active members
        members_res = supabase.table("team_members").select("discord_user_id, display_name").eq("is_active", True).execute()
        if not members_res.data:
            await interaction.followup.send("No active team members.")
            return
            
        # Get today's standups
        standups_res = supabase.table("standups").select("user_id").eq("date", today_date).execute()
        submitted_ids = [s["user_id"] for s in standups_res.data] if standups_res.data else []
        
        missed = [m["display_name"] for m in members_res.data if m["discord_user_id"] not in submitted_ids]
        
        if not missed:
            await interaction.followup.send("✅ Everyone has submitted their standup today!")
        else:
            await interaction.followup.send(f"⚠️ **Missing Standups ({len(missed)}):**\n" + "\n".join(f"- {name}" for name in missed))

    @app_commands.command(name="standup-view", description="View recent standups for a team member")
    async def standup_view(self, interaction: discord.Interaction, person: discord.Member):
        await interaction.response.defer()
        res = supabase.table("standups").select("*").eq("user_id", str(person.id)).order("date", desc=True).limit(5).execute()
        
        if not res.data:
            await interaction.followup.send(f"No standups found for {person.display_name}.")
            return
            
        embed = discord.Embed(title=f"Recent Standups: {person.display_name}", color=0x3498DB)
        for s in res.data:
            val = f"**Yesterday:** {s['yesterday']}\n**Today:** {s['today']}\n**Blockers:** {s['blockers']}"
            if len(val) > 1024:
                val = val[:1021] + "..."
            embed.add_field(name=s["date"], value=val, inline=False)
            
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Standups(bot))
