import discord
from discord.ext import commands
from discord import app_commands
import io
from datetime import datetime, timezone
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from config import supabase
from utils import to_ist, format_duration

class Reporting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mystats", description="See a quick summary of your work history")
    async def mystats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        result = supabase.table("completed_sessions").select("*").eq("user_id", user_id).order("clock_in", desc=False).execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send("No completed sessions found.", ephemeral=True)
            return

        total_seconds = sum(s["duration_seconds"] for s in sessions)
        recent = sessions[-5:]

        embed = discord.Embed(
            title=f"📊 Stats for {interaction.user.display_name}",
            color=0x2979FF
        )
        embed.add_field(
            name="Total Time Logged",
            value=f"{format_duration(total_seconds)} across {len(sessions)} session(s)",
            inline=False
        )
        for s in reversed(recent):
            ci_ist = to_ist(datetime.fromisoformat(s["clock_in"]))
            dur = format_duration(s["duration_seconds"])
            embed.add_field(
                name=f"{ci_ist.strftime('%b %d, %H:%M')} IST — {dur}",
                value=s["description"][:100] + ("..." if len(s["description"]) > 100 else ""),
                inline=False
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="teamstatus", description="See who is currently clocked in")
    async def teamstatus(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = supabase.table("active_sessions").select("*").execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send("Nobody is currently clocked in.", ephemeral=True)
            return

        embed = discord.Embed(title="👥 Currently Working", color=0x00BFA5)
        now_utc = datetime.now(timezone.utc)
        for session in sessions:
            ci_utc = datetime.fromisoformat(session["clock_in"])
            ci_ist = to_ist(ci_utc)
            elapsed = format_duration(int((now_utc - ci_utc).total_seconds()))
            embed.add_field(
                name=session["username"],
                value=f"Clocked in at `{ci_ist.strftime('%H:%M:%S')} IST` ({elapsed} ago)",
                inline=False
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="myreport", description="See your full personal time report with monthly breakdown")
    async def myreport(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        result = supabase.table("completed_sessions").select("*").eq("user_id", user_id).order("clock_in", desc=False).execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send("You have no completed sessions yet.", ephemeral=True)
            return

        total_seconds = sum(s["duration_seconds"] for s in sessions)

        monthly = {}
        for s in sessions:
            mk = s["month_key"]
            monthly[mk] = monthly.get(mk, 0) + s["duration_seconds"]

        embed = discord.Embed(
            title=f"📋 Personal Report — {interaction.user.display_name}",
            color=0x2979FF
        )
        embed.add_field(
            name="🕐 Total Time Logged (This Month)",
            value=f"`{format_duration(total_seconds)}` across `{len(sessions)}` session(s)",
            inline=False
        )

        sorted_months = sorted(monthly.items())
        monthly_lines = []
        for mk, secs in sorted_months:
            try:
                label = datetime.strptime(mk, "%Y-%m").strftime("%B %Y")
            except ValueError:
                label = mk
            monthly_lines.append(f"**{label}:** {format_duration(secs)}")

        embed.add_field(
            name="📅 Monthly Breakdown",
            value="\n".join(monthly_lines) if monthly_lines else "No data",
            inline=False
        )

        recent = sessions[-5:]
        session_lines = []
        for s in reversed(recent):
            ci_ist = to_ist(datetime.fromisoformat(s["clock_in"]))
            dur = format_duration(s["duration_seconds"])
            date_str = ci_ist.strftime("%b %d, %Y at %H:%M IST")
            preview = s["description"][:80] + ("..." if len(s["description"]) > 80 else "")
            session_lines.append(f"**{date_str}** — {dur}\n_{preview}_")

        embed.add_field(
            name="🔍 Last 5 Sessions",
            value="\n\n".join(session_lines) if session_lines else "None",
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="lifetimehours", description="See your total hours worked since day one across all months")
    async def lifetimehours(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        current_result = supabase.table("completed_sessions").select("duration_seconds, clock_in, month_key").eq("user_id", user_id).execute()
        archived_result = supabase.table("archived_sessions").select("duration_seconds, clock_in, month_key").eq("user_id", user_id).execute()

        current_sessions = current_result.data or []
        archived_sessions = archived_result.data or []
        all_sessions = archived_sessions + current_sessions

        if not all_sessions:
            await interaction.followup.send(
                "You have no recorded sessions at all yet. Start clocking in to build your history!",
                ephemeral=True
            )
            return

        total_seconds = sum(s["duration_seconds"] for s in all_sessions)

        monthly = {}
        for s in all_sessions:
            mk = s["month_key"]
            monthly[mk] = monthly.get(mk, 0) + s["duration_seconds"]

        sorted_months = sorted(monthly.items())
        monthly_lines = []
        for mk, secs in sorted_months:
            try:
                label = datetime.strptime(mk, "%Y-%m").strftime("%B %Y")
            except ValueError:
                label = mk
            monthly_lines.append(f"**{label}:** {format_duration(secs)}")

        embed = discord.Embed(
            title=f"🏅 Lifetime Hours — {interaction.user.display_name}",
            description="Every hour you have ever logged since day one.",
            color=0xFF6D00
        )
        embed.add_field(
            name="⏱️ Grand Total",
            value=f"`{format_duration(total_seconds)}`",
            inline=False
        )
        embed.add_field(
            name="📆 Total Sessions",
            value=f"`{len(all_sessions)}` session(s) across `{len(sorted_months)}` month(s)",
            inline=False
        )
        embed.add_field(
            name="📅 Breakdown by Month",
            value="\n".join(monthly_lines) if monthly_lines else "No data",
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="serverreport", description="See total hours logged by everyone, with a chart")
    async def serverreport(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = supabase.table("completed_sessions").select("*").execute()
        sessions = result.data

        if not sessions:
            await interaction.followup.send("No sessions have been logged yet.")
            return

        user_totals = {}
        for s in sessions:
            uid = s["user_id"]
            if uid not in user_totals:
                user_totals[uid] = {"username": s["username"], "seconds": 0}
            user_totals[uid]["seconds"] += s["duration_seconds"]

        sorted_users = sorted(user_totals.items(), key=lambda x: x[1]["seconds"], reverse=True)

        embed = discord.Embed(
            title="📊 Server Work Report",
            description=f"{len(sorted_users)} member(s) have logged time",
            color=0x7C4DFF
        )

        medals = ["🥇", "🥈", "🥉"]
        leaderboard_lines = []
        for i, (uid, info) in enumerate(sorted_users):
            medal = medals[i] if i < 3 else f"`#{i + 1}`"
            leaderboard_lines.append(
                f"{medal} **{info['username']}** — `{format_duration(info['seconds'])}`"
            )
        embed.add_field(
            name="🏆 Leaderboard",
            value="\n".join(leaderboard_lines),
            inline=False
        )

        names = [info["username"] for _, info in sorted_users]
        hours = [info["seconds"] / 3600 for _, info in sorted_users]
        bar_palette = ["#7C4DFF", "#536DFE", "#448AFF", "#40C4FF", "#18FFFF",
                       "#00E5FF", "#00B0FF", "#0091EA", "#304FFE", "#651FFF"]
        bar_colors = [bar_palette[i % len(bar_palette)] for i in range(len(names))]
        fig_width = max(7, len(names) * 1.4)
        fig = Figure(figsize=(fig_width, 5))
        canvas = FigureCanvas(fig)
        bg_color = "#2b2d31"
        fig.patch.set_facecolor(bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1e1f22")
        bars = ax.bar(names, hours, color=bar_colors, width=0.55, zorder=2)
        ax.set_title("Total Hours Worked — All Members", fontsize=13,
                     color="white", pad=14, fontweight="bold")
        ax.set_ylabel("Hours", fontsize=11, color="#b5bac1")
        ax.set_xlabel("Team Member", fontsize=11, color="#b5bac1")
        ax.tick_params(axis="x", colors="white", labelsize=10)
        ax.tick_params(axis="y", colors="#b5bac1", labelsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#3f4147")
        ax.spines["bottom"].set_color("#3f4147")
        ax.grid(axis="y", color="#3f4147", linestyle="--", linewidth=0.7, zorder=1)
        for bar, h in zip(bars, hours):
            label_h = int(h)
            label_m = int((h - label_h) * 60)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(hours) * 0.015,
                f"{label_h}h {label_m}m",
                ha="center", va="bottom", fontsize=9, color="white", fontweight="bold"
            )
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=bg_color)
        buf.seek(0)
        chart_file = discord.File(buf, filename="server_report.png")
        embed.set_image(url="attachment://server_report.png")
        await interaction.followup.send(embed=embed, file=chart_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reporting(bot))
