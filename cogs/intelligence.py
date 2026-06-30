import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import time

from config import supabase, config
from utils import log_event
from ai_engine import jarvis_ai

class Intelligence(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_query_time = 0

    @app_commands.command(name="context", description="View the current context state of a team member")
    async def context(self, interaction: discord.Interaction, person: discord.Member):
        await interaction.response.defer()
        
        user_id_str = str(person.id)
        
        # Gather active tasks
        tasks_res = supabase.table("tasks").select("id, title, status").eq("assignee_id", user_id_str).neq("status", "done").execute()
        active_tasks = tasks_res.data if tasks_res.data else []
        
        # Gather recent blockers
        blockers_res = supabase.table("blockers").select("description, status").eq("reporter_id", user_id_str).eq("status", "open").execute()
        open_blockers = blockers_res.data if blockers_res.data else []
        
        # Gather recent log events (last 5)
        logs_res = supabase.table("context_log").select("event_type, content, created_at").eq("user_id", user_id_str).order("created_at", desc=True).limit(5).execute()
        recent_logs = logs_res.data if logs_res.data else []
        
        embed = discord.Embed(title=f"Context: {person.display_name}", color=0x2ECC71)
        
        tasks_text = "\n".join([f"- {t['title']} ({t['status']})" for t in active_tasks]) or "No active tasks"
        embed.add_field(name="Active Tasks", value=tasks_text, inline=False)
        
        blockers_text = "\n".join([f"- {b['description']}" for b in open_blockers]) or "No open blockers"
        embed.add_field(name="Open Blockers", value=blockers_text, inline=False)
        
        logs_text = "\n".join([f"`{l['event_type']}`: {l['content'][:60]}" for l in recent_logs]) or "No recent activity"
        embed.add_field(name="Recent Activity", value=logs_text, inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="context-task", description="View the context history of a specific task")
    async def context_task(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer()
        
        # Get task details
        task_res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not task_res.data:
            await interaction.followup.send("❌ Task not found.")
            return
            
        task = task_res.data[0]
        
        # Get task updates
        updates_res = supabase.table("task_updates").select("update_text, created_at, user_id").eq("task_id", task_id).order("created_at", desc=True).execute()
        
        # Get blockers linked
        blockers_res = supabase.table("blockers").select("description, status").eq("task_id", task_id).execute()
        
        embed = discord.Embed(title=f"Task Context: {task['title']}", description=task.get('description', 'No description'), color=0x9B59B6)
        embed.add_field(name="Status", value=task['status'])
        
        updates_text = "\n".join([f"- {u['update_text'][:50]}" for u in (updates_res.data or [])[:5]]) or "No progress updates"
        embed.add_field(name="Recent Updates", value=updates_text, inline=False)
        
        blockers_text = "\n".join([f"- {b['description']} ({b['status']})" for b in (blockers_res.data or [])]) or "No linked blockers"
        embed.add_field(name="Linked Blockers", value=blockers_text, inline=False)
        
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
            
        if message.channel.id != config.OPS_BRAIN_CHANNEL_ID:
            return
            
        if self.bot.user in message.mentions:
            now = time.time()
            if now - self.last_query_time < 30:
                await message.reply("⏳ Please wait a moment before asking another question (Rate Limit: 1 per 30s).")
                return
                
            self.last_query_time = now
            
            async with message.channel.typing():
                query = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                response = await jarvis_ai.respond_to_query(query)
                await message.reply(response)

    @app_commands.command(name="profile", description="Generate an AI performance profile for a team member")
    async def profile(self, interaction: discord.Interaction, person: discord.Member):
        await interaction.response.defer()
        response = await jarvis_ai.generate_profile(str(person.id), person.display_name)
        embed = discord.Embed(title=f"🤖 AI Profile: {person.display_name}", description=response, color=0xF1C40F)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="delivery-check", description="Ask Jarvis to predict delivery for a module")
    async def delivery_check(self, interaction: discord.Interaction, module_id: str, target_date: str):
        await interaction.response.defer()
        response = await jarvis_ai.delivery_check(module_id, target_date)
        embed = discord.Embed(title="🚀 AI Delivery Prediction", description=response, color=0xE67E22)
        await interaction.followup.send(embed=embed)
        
    @app_commands.command(name="bottlenecks", description="Ask Jarvis to analyze recent bottlenecks")
    async def bottlenecks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = await jarvis_ai.respond_to_query("Analyze the recent context and identify the biggest bottlenecks or slip reasons.")
        embed = discord.Embed(title="🚧 AI Bottleneck Analysis", description=response, color=0xE74C3C)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Intelligence(bot))
