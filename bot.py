import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from discord import app_commands
# pyrefly: ignore [missing-import]
import asyncpg
import config
from utils.embeds import error_embed

class WorkClockBot(commands.Bot):
    def __init__(self):
        # We only need standard default intents for Slash Commands
        intents = discord.Intents.default()
        # Disable privileged members intent to allow clean connection without Developer Portal toggling
        intents.members = False
        
        super().__init__(
            command_prefix="wc!",
            intents=intents,
            help_command=None
        )
        self.db_pool = None

    async def setup_hook(self):
        """
        Runs before the bot connects to Discord.
        Ideal for initializing database pools, loading extensions, and syncing commands.
        """
        print("Initializing database connection pool...")
        try:
            self.db_pool = await asyncpg.create_pool(
                dsn=config.SUPABASE_DB_URL,
                min_size=1,
                max_size=10,
                ssl='require',
                statement_cache_size=0
            )
            print("Database pool established successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to establish database pool: {e}")
            raise e

        # Load Cogs
        initial_extensions = [
            "cogs.clock",
            "cogs.reports",
            "cogs.leaderboard"
        ]
        
        print("Loading extensions...")
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"Extension '{ext}' successfully loaded.")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

        # Sync slash commands
        print("Syncing slash commands globally...")
        try:
            synced = await self.tree.sync()
            print(f"Successfully synced {len(synced)} slash commands globally.")
        except Exception as e:
            print(f"Failed to sync slash commands globally: {e}")

        # Start keep-awake web server
        self.loop.create_task(self.start_keep_awake_server())

    async def start_keep_awake_server(self):
        """
        Starts a lightweight aiohttp web server on the bound PORT (default 8080).
        This is used to satisfy Render's free tier HTTP port binding requirement and
        allow keep-awake pinging.
        """
        # pyrefly: ignore [missing-import]
        from aiohttp import web
        import os

        async def handle(request):
            return web.Response(text="WorkClock Bot is active and running!")

        app = web.Application()
        app.router.add_get("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()

        # Render dynamically assigns a PORT environment variable
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        
        try:
            await site.start()
            print(f"Keep-awake web server successfully started on port {port}")
        except Exception as e:
            print(f"Failed to start keep-awake web server: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("WorkClock is active and ready for work time-tracking.")
        
        # Simple status: "Watching over work clock sessions"
        activity = discord.Activity(type=discord.ActivityType.watching, name="over work clock sessions")
        await self.change_presence(activity=activity)

    async def close(self):
        """
        Clean shutdown behavior.
        """
        print("Shutting down bot...")
        if self.db_pool:
            print("Closing database pool...")
            await self.db_pool.close()
            print("Database pool closed cleanly.")
        await super().close()

# Instantiate the bot
bot = WorkClockBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Global error handler for Slash Commands (App Commands).
    """
    # Extract original error if wrapped
    orig_error = getattr(error, "original", error)
    
    # Check for database/pg errors
    if isinstance(orig_error, asyncpg.PostgresError):
        print(f"Database PostgresError inside command '{interaction.command.name if interaction.command else 'Unknown'}': {orig_error}")
        embed = error_embed(
            "Database Connection Issue",
            "A database connection or query error occurred. Please contact the administrator to verify PostgreSQL / Supabase server status."
        )
    else:
        print(f"Error in command '{interaction.command.name if interaction.command else 'Unknown'}': {orig_error}")
        embed = error_embed(
            "Application Error",
            f"An unexpected error occurred while executing this command:\n`{str(orig_error)}`"
        )
        
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Failed to send command error response: {e}")

def main():
    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.LoginFailure:
        print("CRITICAL ERROR: Failed to log in. Please check if your DISCORD_TOKEN is valid.")
    except Exception as e:
        print(f"CRITICAL ERROR: Uncaught exception in main startup: {e}")

if __name__ == "__main__":
    main()
