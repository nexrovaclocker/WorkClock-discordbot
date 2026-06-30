import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from config import config
from server import health_server
from scheduler import setup_scheduler

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WorkTrackerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        cogs = [
            "cogs.clock",
            "cogs.stats",
            "cogs.editing",
            "cogs.admin",
            "cogs.modules",
            "cogs.tasks",
            "cogs.standups",
            "cogs.blockers",
            "cogs.demo",
            "cogs.intelligence"
        ]
        for cog in cogs:
            await self.load_extension(cog)
            
        setup_scheduler(self)
            
        await self.tree.sync()

bot = WorkTrackerBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandInvokeError):
        if isinstance(error.original, discord.errors.NotFound):
            return
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ Something went wrong. Please try the command again.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "⚠️ Something went wrong. Please try the command again.",
                ephemeral=True
            )
    except Exception:
        pass

@bot.event
async def on_ready():
    asyncio.create_task(health_server())
    print(f"✅ Bot is online as {bot.user}")

if __name__ == "__main__":
    if config.TOKEN:
        bot.run(config.TOKEN)
    else:
        print("❌ Bot TOKEN is not set in environment variables.")
