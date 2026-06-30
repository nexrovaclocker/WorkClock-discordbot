import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="View a complete guide to all Jarvis commands")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Jarvis Help Menu",
            description="Welcome to the WorkTracker system! Here is a complete guide to everything I can do to help you and the team.",
            color=0x2ecc71
        )
        
        embed.add_field(
            name="Time Tracking",
            value="`/clockin` - Start your daily work session.\n`/clockout` - End session and submit summary.\n`/mystats` - View your total hours and sessions.\n`/edit-session` - (Admin/Founder) Edit a logged session.",
            inline=False
        )
        
        embed.add_field(
            name="Project & Module Management",
            value="`/module-create` - (Founders) Create a new project module.\n`/module-list` - View all active modules.\n`/demo-create` - (Founders) Register a new demo feature.\n`/demo-update` - Update a feature's readiness.",
            inline=False
        )
        
        embed.add_field(
            name="Task System",
            value="`/task-create` - (Founders) Create a new task.\n`/task-list` - View open tasks for a module.\n`/task-claim` - Assign an open task to yourself.\n`/task-assign` - (Founders) Delegate a task.\n`/task-start` - Move a task to in_progress.\n`/task-done` - Mark a task as completed.\n`/task-slip` - Report a task deadline slip.",
            inline=False
        )
        
        embed.add_field(
            name="Blockers & Operations",
            value="`/standup` - Submit your daily standup.\n`/blocker-report` - Report a blocker (pings blocking person).\n`/blocker-resolve` - Mark a blocker as resolved.\n`/blocker-list` - View all active blockers.",
            inline=False
        )
        
        embed.add_field(
            name="AI Intelligence (Ops-Brain)",
            value="*Note: You can also mention @Jarvis in #ops-brain to talk directly.*\n`/profile` - Generate performance analysis of a user.\n`/delivery-check` - Predict if a module is on track.\n`/bottlenecks` - Analyze team's recent slip reasons.\n`/context` - View raw recent logs for a person.",
            inline=False
        )
        
        embed.add_field(
            name="System Admin",
            value="`/jarvis-status` - (Admin) Check DB health and Azure OpenAI.\n`/context-add` - (Admin) Manually inject info into Jarvis.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
