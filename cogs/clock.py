import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from discord import app_commands
import database
import config
from utils.embeds import success_embed, error_embed, info_embed
import pytz
from datetime import datetime

def format_local_time(dt: datetime, tz_name: str) -> str:
    """
    Formats a datetime in the given timezone into a user-friendly 12-hour format.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    local_dt = dt.astimezone(pytz.timezone(tz_name))
    return local_dt.strftime("%I:%M %p")

class ClockCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clockin", description="Start a work session")
    async def clockin(self, interaction: discord.Interaction):
        # Acknowledge the interaction
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        username = interaction.user.display_name
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            # Check for existing open session
            open_sess = await database.get_open_session(self.bot.db_pool, user_id, guild_id)
            if open_sess:
                clock_in_formatted = format_local_time(open_sess["clock_in_time"], config.TIMEZONE)
                embed = error_embed(
                    "Already Clocked In",
                    f"You already have an active work session! You clocked in at **{clock_in_formatted}**.\n"
                    f"Please clock out using `/clockout` before starting a new session."
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Start new session
            new_sess = await database.create_session(
                self.bot.db_pool, user_id, username, guild_id, config.TIMEZONE
            )
            clock_in_formatted = format_local_time(new_sess["clock_in_time"], config.TIMEZONE)
            
            embed = success_embed(
                "Clocked In!",
                f"Your work session has started.\n"
                f"**Time:** {clock_in_formatted} (IST)\n"
                f"**Date:** {new_sess['date'].strftime('%Y-%m-%d')}"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="clockout", description="End the active session")
    @app_commands.describe(work_done="Describe what work you accomplished during this session (required)")
    async def clockout(self, interaction: discord.Interaction, work_done: str):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        try:
            # Check if clocked in
            open_sess = await database.get_open_session(self.bot.db_pool, user_id, guild_id)
            if not open_sess:
                embed = error_embed(
                    "Not Clocked In",
                    "You do not have an active work session. Use `/clockin` to start working!"
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Close session
            closed_sess = await database.close_session(
                self.bot.db_pool, open_sess["id"], open_sess["clock_in_time"]
            )
            
            total_minutes = float(closed_sess["duration_minutes"])
            hours = int(total_minutes // 60)
            mins = int(total_minutes % 60)
            duration_str = f"**{hours}h {mins}m**" if hours > 0 else f"**{mins}m**"
            
            clock_in_str = format_local_time(closed_sess["clock_in_time"], config.TIMEZONE)
            clock_out_str = format_local_time(closed_sess["clock_out_time"], config.TIMEZONE)
            
            embed = success_embed(
                "Clocked Out!",
                f"Successfully saved your work session.\n"
                f"**Clocked In:** {clock_in_str}\n"
                f"**Clocked Out:** {clock_out_str}\n"
                f"**Total Duration:** {duration_str}"
            )
            embed.add_field(name="Work Done Summary", value=work_done, inline=False)
                
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="editlast", description="Edit your last completed session's clock-in or clock-out times")
    @app_commands.describe(
        clock_in="New clock-in time (e.g., '09:30 AM', '14:15', or 'YYYY-MM-DD HH:MM')",
        clock_out="New clock-out time (e.g., '06:00 PM', '18:00', or 'YYYY-MM-DD HH:MM')"
    )
    async def editlast(self, interaction: discord.Interaction, clock_in: str = None, clock_out: str = None):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        if not clock_in and not clock_out:
            embed = error_embed(
                "No Changes Provided",
                "Please specify at least one of `clock_in` or `clock_out` to edit your last session."
            )
            await interaction.followup.send(embed=embed)
            return
            
        try:
            # Get last completed session
            last_sess = await database.get_last_completed_session(self.bot.db_pool, user_id, guild_id)
            if not last_sess:
                embed = error_embed(
                    "No Completed Sessions",
                    "We couldn't find any completed work sessions for you in this server."
                )
                await interaction.followup.send(embed=embed)
                return
                
            local_tz = pytz.timezone(config.TIMEZONE)
            session_date = last_sess["date"] # a datetime.date
            
            # Helper to parse inputs in local timezone
            def parse_time_input(input_str: str, default_dt: datetime) -> datetime:
                input_str = input_str.strip()
                # Try full formats first (with date)
                for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        parsed = datetime.strptime(input_str, fmt)
                        return local_tz.localize(parsed)
                    except ValueError:
                        pass
                
                # Try time-only formats and combine with original session date
                for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M"):
                    try:
                        parsed_time = datetime.strptime(input_str, fmt).time()
                        combined = datetime.combine(session_date, parsed_time)
                        return local_tz.localize(combined)
                    except ValueError:
                        pass
                        
                raise ValueError(f"Unable to parse time/date string: `{input_str}`")

            # Determine new times
            orig_in = last_sess["clock_in_time"]
            orig_out = last_sess["clock_out_time"]
            
            # Ensure aware of UTC
            if orig_in.tzinfo is None:
                orig_in = orig_in.replace(tzinfo=pytz.utc)
            if orig_out.tzinfo is None:
                orig_out = orig_out.replace(tzinfo=pytz.utc)

            new_in_utc = orig_in
            new_out_utc = orig_out
            
            if clock_in:
                try:
                    new_in_local = parse_time_input(clock_in, orig_in)
                    new_in_utc = new_in_local.astimezone(pytz.utc)
                except ValueError as e:
                    await interaction.followup.send(embed=error_embed("Invalid Clock-In Time", str(e)))
                    return
                    
            if clock_out:
                try:
                    new_out_local = parse_time_input(clock_out, orig_out)
                    new_out_utc = new_out_local.astimezone(pytz.utc)
                except ValueError as e:
                    await interaction.followup.send(embed=error_embed("Invalid Clock-Out Time", str(e)))
                    return
                    
            # Validations
            if new_in_utc >= new_out_utc:
                embed = error_embed(
                    "Invalid Timings",
                    f"New clock-in time must be **before** the new clock-out time.\n"
                    f"**Clock-in:** {format_local_time(new_in_utc, config.TIMEZONE)}\n"
                    f"**Clock-out:** {format_local_time(new_out_utc, config.TIMEZONE)}"
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Compute new duration
            duration = new_out_utc - new_in_utc
            duration_minutes = round(duration.total_seconds() / 60.0, 2)
            
            # Limit duration to a reasonable max (e.g. 24 hours) to prevent fat-finger entry errors
            if duration_minutes > 1440:
                embed = error_embed(
                    "Duration Too Long",
                    "A single work session cannot be longer than 24 hours. Please double check your dates and times."
                )
                await interaction.followup.send(embed=embed)
                return
                
            # Update database
            updated_sess = await database.update_session_times(
                self.bot.db_pool, last_sess["id"], new_in_utc, new_out_utc, duration_minutes
            )
            
            hours = int(duration_minutes // 60)
            mins = int(duration_minutes % 60)
            duration_str = f"**{hours}h {mins}m**" if hours > 0 else f"**{mins}m**"
            
            embed = success_embed(
                "Session Updated Successfully!",
                f"Your most recent completed work session has been updated.\n\n"
                f"📅 **Date:** {updated_sess['date'].strftime('%Y-%m-%d')}\n"
                f"📥 **Clocked In:** {format_local_time(new_in_utc, config.TIMEZONE)}\n"
                f"📤 **Clocked Out:** {format_local_time(new_out_utc, config.TIMEZONE)}\n"
                f"⏱️ **New Duration:** {duration_str}"
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.dispatch("app_command_error", interaction, e)

    @app_commands.command(name="status", description="See your current session state and live duration")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "DM"
        
        # Get all open sessions for the guild
        open_sessions = await database.get_all_open_sessions(self.bot.db_pool, guild_id)
        if not open_sessions:
            embed = info_embed(
                "WorkClock Status",
                "No members are currently clocked in."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Build a list of active users with their clock-in times
        lines = []
        for sess in open_sessions:
            user_name = sess["username"]
            clock_in_time = format_local_time(sess["clock_in_time"], config.TIMEZONE)
            lines.append(f"• **{user_name}** – Clocked in at **{clock_in_time}** (IST)")
        
        embed = info_embed("WorkClock Status", "Active clock‑in sessions:")
        embed.description = "\n".join(lines)
        await interaction.followup.send(embed=embed)
        return

async def setup(bot: commands.Bot):
    await bot.add_cog(ClockCog(bot))
