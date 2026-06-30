import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase
from utils import to_ist, format_duration, get_month_key, IST_OFFSET

class Editing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="editsessions", description="View your recent sessions so you can find which one to edit")
    async def editsessions(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        result = supabase.table("completed_sessions").select("*").eq("user_id", user_id).order("clock_in", desc=False).execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send("You have no completed sessions to edit.", ephemeral=True)
            return

        recent = sessions[-10:]
        lines = []
        total = len(sessions)
        for i, s in enumerate(reversed(recent)):
            real_index = total - i
            ci_ist = to_ist(datetime.fromisoformat(s["clock_in"]))
            co_ist = to_ist(datetime.fromisoformat(s["clock_out"]))
            dur = format_duration(s["duration_seconds"])
            lines.append(f"`#{real_index}` — **{ci_ist.strftime('%Y-%m-%d %H:%M IST')}** → **{co_ist.strftime('%H:%M IST')}** ({dur})")

        embed = discord.Embed(
            title="🗂️ Your Recent Sessions",
            description=(
                "Below are your last 10 sessions.\n"
                "To edit one, use:\n"
                "`/edittime session_number:<number> field:<clock_in or clock_out> new_time:<YYYY-MM-DD HH:MM>`\n"
                "⚠️ Enter times in **IST**.\n\n"
                + "\n".join(lines)
            ),
            color=0xFFA000
        )
        embed.set_footer(text="Times shown and entered in IST.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="edittime", description="Edit the clock-in or clock-out time of a past session")
    @app_commands.describe(
        session_number="The session number shown by /editsessions",
        field="Which time to change: clock_in or clock_out",
        new_time="New time in IST, format: YYYY-MM-DD HH:MM (e.g. 2024-06-01 09:30)"
    )
    @app_commands.choices(field=[
        app_commands.Choice(name="clock_in", value="clock_in"),
        app_commands.Choice(name="clock_out", value="clock_out")
    ])
    async def edittime(
        self,
        interaction: discord.Interaction,
        session_number: int,
        field: str,
        new_time: str
    ):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        result = supabase.table("completed_sessions").select("*").eq("user_id", user_id).order("clock_in", desc=False).execute()
        user_sessions = result.data

        if not user_sessions:
            await interaction.followup.send("You have no completed sessions to edit.", ephemeral=True)
            return

        total = len(user_sessions)
        if session_number < 1 or session_number > total:
            await interaction.followup.send(
                f"❌ Invalid session number. You have `{total}` session(s). Run `/editsessions` to see them.",
                ephemeral=True
            )
            return

        try:
            new_dt_ist = datetime.strptime(new_time, "%Y-%m-%d %H:%M")
            new_dt_utc = new_dt_ist.replace(tzinfo=timezone.utc) - IST_OFFSET
        except ValueError:
            await interaction.followup.send(
                "❌ Invalid format. Please use `YYYY-MM-DD HH:MM` in IST — for example: `2024-06-01 09:30`",
                ephemeral=True
            )
            return

        target = user_sessions[session_number - 1]
        record_id = target["id"]
        old_clock_in_utc = datetime.fromisoformat(target["clock_in"])
        old_clock_out_utc = datetime.fromisoformat(target["clock_out"])

        if field == "clock_in":
            if new_dt_utc >= old_clock_out_utc:
                old_co_ist = to_ist(old_clock_out_utc)
                await interaction.followup.send(
                    f"❌ The new clock-in (`{new_time} IST`) must be before clock-out "
                    f"(`{old_co_ist.strftime('%Y-%m-%d %H:%M')} IST`).",
                    ephemeral=True
                )
                return
            old_value_str = to_ist(old_clock_in_utc).strftime("%Y-%m-%d %H:%M IST")
            new_clock_in_utc = new_dt_utc
            new_clock_out_utc = old_clock_out_utc
        else:
            if new_dt_utc <= old_clock_in_utc:
                old_ci_ist = to_ist(old_clock_in_utc)
                await interaction.followup.send(
                    f"❌ The new clock-out (`{new_time} IST`) must be after clock-in "
                    f"(`{old_ci_ist.strftime('%Y-%m-%d %H:%M')} IST`).",
                    ephemeral=True
                )
                return
            old_value_str = to_ist(old_clock_out_utc).strftime("%Y-%m-%d %H:%M IST")
            new_clock_in_utc = old_clock_in_utc
            new_clock_out_utc = new_dt_utc

        new_total_seconds = int((new_clock_out_utc - new_clock_in_utc).total_seconds())
        new_month_key = get_month_key(new_clock_in_utc)

        supabase.table("completed_sessions").update({
            field: new_dt_utc.isoformat(),
            "duration_seconds": new_total_seconds,
            "month_key": new_month_key
        }).eq("id", record_id).execute()

        embed = discord.Embed(title="✏️ Session Updated", color=0x00C853)
        embed.add_field(name="Session", value=f"#{session_number}", inline=True)
        embed.add_field(name="Field Changed", value=field.replace("_", " ").title(), inline=True)
        embed.add_field(name="Old Value", value=old_value_str, inline=False)
        embed.add_field(name="New Value", value=f"{new_time} IST", inline=False)
        embed.add_field(name="Recalculated Duration", value=format_duration(new_total_seconds), inline=False)
        embed.set_footer(text="Your log has been updated.")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Editing(bot))
