import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase
from utils import require_founder, to_ist, IST_OFFSET, format_duration, log_event
import uuid

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

class TaskCreateModal(discord.ui.Modal, title="Create Task"):
    title_input = discord.ui.TextInput(label="Task Title", max_length=150)
    module_id_input = discord.ui.TextInput(label="Module ID", placeholder="Copy from /module-list")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)
    estimate = discord.ui.TextInput(label="Estimated Hours", placeholder="e.g. 2.5", required=False)
    due_date = discord.ui.TextInput(label="Due Date (YYYY-MM-DD)", placeholder="e.g. 2025-06-01", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        dt_utc = None
        if self.due_date.value:
            try:
                dt_ist = datetime.strptime(self.due_date.value.strip(), "%Y-%m-%d")
                dt_utc = dt_ist.replace(tzinfo=timezone.utc) - IST_OFFSET
            except ValueError:
                await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
                return
        
        est_hours = None
        if self.estimate.value:
            try:
                est_hours = float(self.estimate.value)
            except ValueError:
                await interaction.response.send_message("❌ Invalid estimate. Use a number (e.g. 2.5).", ephemeral=True)
                return

        data = {
            "title": str(self.title_input),
            "module_id": str(self.module_id_input).strip() or None,
            "description": str(self.description) if self.description.value else None,
            "estimated_hours": est_hours,
            "due_date": dt_utc.isoformat() if dt_utc else None,
            "creator_id": str(interaction.user.id)
        }
        
        # Verify module
        if data["module_id"]:
            mod_res = supabase.table("modules").select("id").eq("id", data["module_id"]).execute()
            if not mod_res.data:
                await interaction.response.send_message("❌ Module ID not found.", ephemeral=True)
                return

        res = supabase.table("tasks").insert(data).execute()
        if not res.data:
            await interaction.response.send_message("❌ Failed to create task.", ephemeral=True)
            return
            
        task_id = res.data[0]["id"]
        log_event("task_create", str(interaction.user.id), f"Created task: {self.title_input}", task_id=task_id, module_id=data["module_id"])
        await interaction.response.send_message(f"✅ Task created! ID: `{task_id}`", ephemeral=False)

class SlipReasonModal(discord.ui.Modal, title="Task Slippage Reason"):
    reason_cat = discord.ui.TextInput(label="Category (dependency, underestimate, etc.)", max_length=50)
    reason_text = discord.ui.TextInput(label="Explain what happened", style=discord.TextStyle.paragraph)

    def __init__(self, task, original_due, new_due):
        super().__init__()
        self.task = task
        self.original_due = original_due
        self.new_due = new_due

    async def on_submit(self, interaction: discord.Interaction):
        supabase.table("slip_reasons").insert({
            "task_id": self.task["id"],
            "user_id": str(interaction.user.id),
            "original_due_date": self.original_due.isoformat() if self.original_due else None,
            "new_due_date": self.new_due.isoformat() if self.new_due else None,
            "reason_category": str(self.reason_cat),
            "reason_text": str(self.reason_text)
        }).execute()
        
        supabase.table("tasks").update({
            "status": "done",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", self.task["id"]).execute()
        
        log_event("task_slip", str(interaction.user.id), f"Slipped task '{self.task['title']}' due to: {self.reason_cat}", task_id=self.task["id"])
        
        await interaction.response.send_message(f"✅ Slip reason recorded and task `{self.task['title']}` marked done.", ephemeral=False)

class TaskUpdateModal(discord.ui.Modal, title="Add Progress Note"):
    note = discord.ui.TextInput(label="What's the update?", style=discord.TextStyle.paragraph)

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    async def on_submit(self, interaction: discord.Interaction):
        supabase.table("task_updates").insert({
            "task_id": self.task_id,
            "user_id": str(interaction.user.id),
            "update_text": str(self.note)
        }).execute()
        await interaction.response.send_message("✅ Progress note added.", ephemeral=True)


class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="task-create", description="Create a new task")
    async def task_create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TaskCreateModal())

    @app_commands.command(name="task-assign", description="Founder only: Assign a task to someone")
    @require_founder()
    async def task_assign(self, interaction: discord.Interaction, task_id: str, person: discord.Member):
        await interaction.response.defer()
        if not is_valid_uuid(task_id):
            await interaction.followup.send("❌ Invalid Task ID format.")
            return
        res = supabase.table("tasks").update({"assignee_id": str(person.id)}).eq("id", task_id).execute()
        if not res.data:
            await interaction.followup.send("❌ Task not found.")
            return
            
        log_event("task_assign", str(interaction.user.id), f"Assigned task to {person.display_name}", task_id=task_id)
        await interaction.followup.send(f"✅ Assigned task to **{person.display_name}**.")

    @app_commands.command(name="task-start", description="Mark your assigned task as in progress")
    async def task_start(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer()
        if not is_valid_uuid(task_id):
            await interaction.followup.send("❌ Invalid Task ID format.")
            return
        res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not res.data:
            await interaction.followup.send("❌ Task not found.")
            return
        
        task = res.data[0]
        if task["assignee_id"] != str(interaction.user.id):
            await interaction.followup.send("❌ You are not assigned to this task.")
            return

        supabase.table("tasks").update({
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", task_id).execute()
        
        log_event("task_start", str(interaction.user.id), f"Started working on {task['title']}", task_id=task_id)
        await interaction.followup.send(f"✅ Started working on **{task['title']}**.")

    @app_commands.command(name="task-done", description="Mark a task complete")
    async def task_done(self, interaction: discord.Interaction, task_id: str):
        if not is_valid_uuid(task_id):
            await interaction.response.send_message("❌ Invalid Task ID format.", ephemeral=True)
            return
        res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not res.data:
            await interaction.response.send_message("❌ Task not found.", ephemeral=True)
            return
        
        task = res.data[0]
        if task["assignee_id"] != str(interaction.user.id) and not utils.is_founder(str(interaction.user.id)):
            await interaction.response.send_message("❌ You are not assigned to this task.", ephemeral=True)
            return

        now_utc = datetime.now(timezone.utc)
        is_slipped = False
        if task["due_date"]:
            due_utc = datetime.fromisoformat(task["due_date"])
            if now_utc > due_utc:
                is_slipped = True

        if is_slipped:
            # Need reason
            supabase.table("tasks").update({
                "slipped": True,
                "slip_count": task.get("slip_count", 0) + 1
            }).eq("id", task_id).execute()
            await interaction.response.send_modal(SlipReasonModal(task, due_utc, now_utc))
        else:
            supabase.table("tasks").update({
                "status": "done",
                "completed_at": now_utc.isoformat()
            }).eq("id", task_id).execute()
            
            log_event("task_complete", str(interaction.user.id), f"Completed task {task['title']}", task_id=task_id)
            await interaction.response.send_message(f"✅ Task **{task['title']}** marked as complete!", ephemeral=False)

    @app_commands.command(name="task-update", description="Add a progress note")
    async def task_update(self, interaction: discord.Interaction, task_id: str):
        if not is_valid_uuid(task_id):
            await interaction.response.send_message("❌ Invalid Task ID format.", ephemeral=True)
            return
        await interaction.response.send_modal(TaskUpdateModal(task_id))

    @app_commands.command(name="my-tasks", description="View your active tasks")
    async def my_tasks(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        res = supabase.table("tasks").select("*").eq("assignee_id", str(interaction.user.id)).neq("status", "done").execute()
        if not res.data:
            await interaction.followup.send("You have no open tasks.", ephemeral=True)
            return
            
        embed = discord.Embed(title="📋 My Open Tasks", color=0x2979FF)
        for t in res.data:
            embed.add_field(name=t['title'], value=f"Status: `{t['status']}` | ID: `{t['id'][:8]}`", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="pickup", description="See and claim unassigned tasks")
    async def pickup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        res = supabase.table("tasks").select("*").is_("assignee_id", "null").eq("status", "todo").execute()
        if not res.data:
            await interaction.followup.send("No unassigned tasks right now.", ephemeral=True)
            return
            
        embed = discord.Embed(title="🙋 Unassigned Tasks", color=0x00C853)
        for t in res.data:
            embed.add_field(name=t['title'], value=f"ID: `{t['id']}`", inline=False)
            
        # Simplification: User copies ID and uses a /claim command or we just tell them to ask founders.
        # But Phase 1 says `/pickup` shows list and lets them assign to themselves. We can't do dynamic select menus easily here without views, so let's just add a /task-claim command or just list them.
        embed.set_footer(text="To claim a task, use /task-claim <id>")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="task-claim", description="Claim an unassigned task")
    async def task_claim(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer()
        if not is_valid_uuid(task_id):
            await interaction.followup.send("❌ Invalid Task ID format.")
            return
        res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not res.data:
            await interaction.followup.send("❌ Task not found.")
            return
        if res.data[0].get("assignee_id"):
            await interaction.followup.send("❌ Task is already assigned.")
            return
            
        supabase.table("tasks").update({"assignee_id": str(interaction.user.id)}).eq("id", task_id).execute()
        log_event("task_pickup", str(interaction.user.id), f"Claimed task {res.data[0]['title']}", task_id=task_id)
        await interaction.followup.send(f"✅ You claimed **{res.data[0]['title']}**.")

    @app_commands.command(name="task-list", description="List tasks")
    async def task_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        res = supabase.table("tasks").select("*").execute()
        if not res.data:
            await interaction.followup.send("No tasks found.")
            return
        embed = discord.Embed(title="📋 All Tasks", color=0x2979FF)
        for t in res.data[:10]: # Limit to 10 for simplicity
            embed.add_field(name=t['title'], value=f"Status: `{t['status']}` | ID: `{t['id'][:8]}`", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task-view", description="View full task details")
    async def task_view(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer()
        if not is_valid_uuid(task_id):
            await interaction.followup.send("❌ Invalid Task ID format.")
            return
        res = supabase.table("tasks").select("*").eq("id", task_id).execute()
        if not res.data:
            await interaction.followup.send("❌ Task not found.")
            return
        t = res.data[0]
        embed = discord.Embed(title=t['title'], description=t.get('description', 'No description'), color=0x3498DB)
        embed.add_field(name="Status", value=t['status'])
        embed.add_field(name="Assignee", value=t.get('assignee_id', 'Unassigned'))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task-block", description="Mark task as blocked")
    async def task_block(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer()
        if not is_valid_uuid(task_id):
            await interaction.followup.send("❌ Invalid Task ID format.")
            return
        res = supabase.table("tasks").update({"status": "blocked"}).eq("id", task_id).execute()
        if not res.data:
            await interaction.followup.send("❌ Task not found.")
            return
            
        log_event("task_block", str(interaction.user.id), f"Marked task {res.data[0]['title']} as blocked", task_id=task_id)
        await interaction.followup.send(f"⚠️ Task **{res.data[0]['title']}** marked as blocked.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot))
