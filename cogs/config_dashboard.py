import discord
from discord.ext import commands
from discord import app_commands
from config_manager import bot_config
from utils import is_admin, is_founder
from config import supabase

class DMTimeModal(discord.ui.Modal, title="Configure Nightly DM Time"):
    time_input = discord.ui.TextInput(
        label="DM Time (IST)",
        placeholder="HH:MM (e.g. 22:00)",
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        time_str = str(self.time_input).strip()
        # Basic validation
        if len(time_str) != 5 or ":" not in time_str:
            await interaction.response.send_message("❌ Invalid format. Use HH:MM.", ephemeral=True)
            return
            
        settings = bot_config.get_settings()
        settings["daily_dm_time"] = time_str
        bot_config.update_settings(settings)
        await interaction.response.send_message(f"✅ Nightly DM time updated to {time_str} IST.", ephemeral=True)

class AdminsModal(discord.ui.Modal, title="Configure Admins"):
    admin_input = discord.ui.TextInput(
        label="Admin Discord IDs (Comma Separated)",
        style=discord.TextStyle.paragraph
    )

    def __init__(self):
        super().__init__()
        settings = bot_config.get_settings()
        self.admin_input.default = settings.get("admin_ids", "")

    async def on_submit(self, interaction: discord.Interaction):
        settings = bot_config.get_settings()
        settings["admin_ids"] = str(self.admin_input).strip()
        bot_config.update_settings(settings)
        await interaction.response.send_message("✅ Admins updated successfully.", ephemeral=True)

class ConfigSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Schedule & Timers", description="Set the nightly DM time", emoji="⏰", value="timers"),
            discord.SelectOption(label="Permissions", description="Manage Admin IDs", emoji="🛡️", value="permissions"),
        ]
        super().__init__(placeholder="Select a category to configure...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "timers":
            await interaction.response.send_modal(DMTimeModal())
        elif self.values[0] == "permissions":
            if not is_founder(str(interaction.user.id)):
                await interaction.response.send_message("❌ Only founders can change permissions.", ephemeral=True)
                return
            await interaction.response.send_modal(AdminsModal())

class ConfigView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ConfigSelect())

class ConfigDashboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="config", description="Admin only: Open the interactive settings dashboard")
    async def config(self, interaction: discord.Interaction):
        if not is_admin(str(interaction.user.id)):
            await interaction.response.send_message("❌ You do not have permission to view the config dashboard.", ephemeral=True)
            return

        settings = bot_config.get_settings()
        
        embed = discord.Embed(title="⚙️ JARVIS Control Panel", color=0x2B2D31)
        embed.add_field(name="Nightly DM Time", value=f"`{settings.get('daily_dm_time', '22:00')} IST`", inline=False)
        
        admin_count = len([x for x in settings.get("admin_ids", "").split(",") if x])
        embed.add_field(name="Admins", value=f"`{admin_count}` registered", inline=False)
        
        await interaction.response.send_message(embed=embed, view=ConfigView(), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigDashboard(bot))
