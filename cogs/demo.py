import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from config import supabase
from utils import log_event

class DemoAddModal(discord.ui.Modal, title="Add Demo Feature"):
    name = discord.ui.TextInput(label="Feature Name", max_length=100)
    module_id = discord.ui.TextInput(label="Module ID (Optional)", required=False)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "name": str(self.name),
            "description": str(self.description) if self.description.value else None,
            "module_id": str(self.module_id).strip() if self.module_id.value else None,
            "last_updated_by": str(interaction.user.id)
        }
        
        # Verify module
        if data["module_id"]:
            mod_res = supabase.table("modules").select("id").eq("id", data["module_id"]).execute()
            if not mod_res.data:
                await interaction.response.send_message("❌ Module ID not found.", ephemeral=True)
                return
                
        supabase.table("demo_features").insert(data).execute()
        await interaction.response.send_message(f"✅ Feature **{self.name}** added to the next demo.", ephemeral=False)


class DemoUpdateModal(discord.ui.Modal, title="Update Demo Feature"):
    status_note = discord.ui.TextInput(label="Status Note / Details", style=discord.TextStyle.paragraph)

    def __init__(self, feature, status):
        super().__init__()
        self.feature = feature
        self.status = status

    async def on_submit(self, interaction: discord.Interaction):
        supabase.table("demo_features").update({
            "status": self.status,
            "status_note": str(self.status_note),
            "last_updated_by": str(interaction.user.id),
            "last_updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", self.feature["id"]).execute()
        
        log_event("demo_update", str(interaction.user.id), f"Updated feature {self.feature['name']} to {self.status}: {self.status_note}")
        
        await interaction.response.send_message(f"✅ Feature **{self.feature['name']}** updated to `{self.status}`.", ephemeral=False)


class Demo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="demo-add", description="Add a feature to be tracked for the next demo")
    async def demo_add(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DemoAddModal())

    @app_commands.command(name="demo-update", description="Update the readiness of a demo feature")
    @app_commands.describe(status="Status of the feature")
    @app_commands.choices(status=[
        app_commands.Choice(name="Ready", value="ready"),
        app_commands.Choice(name="Partial / Buggy", value="partial"),
        app_commands.Choice(name="Not Ready", value="not_ready")
    ])
    async def demo_update(self, interaction: discord.Interaction, feature_id: str, status: app_commands.Choice[str]):
        res = supabase.table("demo_features").select("*").eq("id", feature_id).execute()
        if not res.data:
            await interaction.response.send_message("❌ Feature not found.", ephemeral=True)
            return
            
        await interaction.response.send_modal(DemoUpdateModal(res.data[0], status.value))

    @app_commands.command(name="demo-ready", description="Check the team's readiness for the next demo")
    async def demo_ready(self, interaction: discord.Interaction):
        await interaction.response.defer()
        res = supabase.table("demo_features").select("*").execute()
        if not res.data:
            await interaction.followup.send("No features are being tracked for the demo right now.")
            return
            
        total = len(res.data)
        ready_count = 0
        partial_count = 0
        
        embed = discord.Embed(title="🚀 Demo Readiness", color=0x9B59B6)
        
        for f in res.data:
            status = f["status"]
            if status == "ready":
                icon = "🟢"
                ready_count += 1
            elif status == "partial":
                icon = "🟡"
                partial_count += 1
            else:
                icon = "🔴"
                
            note = f.get("status_note") or "No notes"
            embed.add_field(name=f"{icon} {f['name']}", value=f"*{note}*\nID: `{f['id'][:8]}`", inline=False)
            
        score = ((ready_count * 1.0) + (partial_count * 0.5)) / total * 100
        
        recommendation = "Ship it! 🚀" if score >= 90 else "Needs some polish. 🛠️" if score >= 60 else "Not ready. ⛔"
        
        embed.description = f"**Overall Readiness:** {score:.1f}%\n**Recommendation:** {recommendation}"
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Demo(bot))
