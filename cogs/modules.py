import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase
from utils import require_founder, to_ist, IST_OFFSET

class ModuleCreateModal(discord.ui.Modal, title="Create Module"):
    name = discord.ui.TextInput(label="Module Name", max_length=100)
    client_name = discord.ui.TextInput(label="Client Name", required=False, max_length=100)
    deadline = discord.ui.TextInput(label="Deadline (YYYY-MM-DD)", required=False, placeholder="e.g. 2025-06-01")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        dt_utc = None
        if self.deadline.value:
            try:
                dt_ist = datetime.strptime(self.deadline.value.strip(), "%Y-%m-%d")
                dt_utc = dt_ist.replace(tzinfo=timezone.utc) - IST_OFFSET
            except ValueError:
                await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
                return

        data = {
            "name": str(self.name),
            "client_name": str(self.client_name) if self.client_name.value else None,
            "description": str(self.description) if self.description.value else None,
            "deadline": dt_utc.isoformat() if dt_utc else None,
            "created_by": str(interaction.user.id)
        }
        supabase.table("modules").insert(data).execute()
        await interaction.response.send_message(f"✅ Module **{self.name}** created successfully.", ephemeral=False)

class Modules(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="module-create", description="Founder only: Create a new project module")
    @require_founder()
    async def module_create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModuleCreateModal())

    @app_commands.command(name="module-list", description="List all active modules")
    async def module_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        res = supabase.table("modules").select("*").eq("status", "active").execute()
        if not res.data:
            await interaction.followup.send("No active modules found.")
            return
            
        embed = discord.Embed(title="📁 Active Modules", color=0x3498DB)
        for mod in res.data:
            desc = mod.get("description") or "No description"
            deadline_str = "No deadline"
            if mod.get("deadline"):
                dl_utc = datetime.fromisoformat(mod["deadline"])
                dl_ist = to_ist(dl_utc)
                deadline_str = f"Due: {dl_ist.strftime('%b %d, %Y')}"
            
            client = f" (Client: {mod['client_name']})" if mod.get("client_name") else ""
            embed.add_field(name=f"{mod['name']}{client}", value=f"{desc}\n_{deadline_str}_", inline=False)
            
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Modules(bot))
