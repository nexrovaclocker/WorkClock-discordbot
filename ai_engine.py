import os
from datetime import datetime, timezone, timedelta
from openai import AsyncAzureOpenAI
from config import config, supabase

class JarvisAI:
    def __init__(self):
        if not config.AZURE_OPENAI_API_KEY or not config.AZURE_OPENAI_ENDPOINT:
            self.client = None
            print("⚠️ Azure OpenAI credentials missing. AI features disabled.")
            return
            
        self.client = AsyncAzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = config.AZURE_OPENAI_DEPLOYMENT

    async def _call_llm(self, system_prompt: str, user_prompt: str = "") -> str:
        if not self.client:
            return "⚠️ AI features are disabled due to missing credentials."
            
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ AI Error: {e}"

    def compile_context(self, days: int = 3, user_id: str = None, module_id: str = None) -> str:
        # Get logs from last X days
        time_threshold = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        context_str = ""
        
        if days > 7 and not user_id and not module_id:
            snap_res = supabase.table("jarvis_snapshots").select("*").gte("created_at", time_threshold).order("created_at", desc=False).execute()
            if snap_res.data:
                context_str += "--- HISTORICAL SNAPSHOTS ---\n"
                for s in snap_res.data:
                    context_str += f"[{s['created_at'][:10]}] {s['summary']}\n"
                context_str += "----------------------------\n"
        
        query = supabase.table("context_log").select("*").gte("created_at", time_threshold).order("created_at", desc=False)
        if user_id:
            query = query.eq("user_id", user_id)
        if module_id:
            query = query.eq("module_id", module_id)
            
        res = query.limit(300).execute() # Hard cap of 300 to protect token limits
        
        if not res.data:
            return "No recent context found."
            
        context_str = ""
        for row in res.data:
            dt = datetime.fromisoformat(row["created_at"]).strftime("%m-%d %H:%M")
            uid = row.get("user_id", "System")
            evt = row["event_type"]
            content = row["content"]
            context_str += f"[{dt}] {uid} ({evt}): {content}\n"
            
        return context_str

    async def morning_briefing(self) -> str:
        context = self.compile_context(days=3)
        with open("prompts/morning_briefing.txt", "r") as f:
            prompt_template = f.read()
            
        prompt = prompt_template.replace("{context}", context)
        return await self._call_llm(prompt)

    async def respond_to_query(self, query: str) -> str:
        context = self.compile_context(days=3)
        with open("prompts/ops_brain.txt", "r") as f:
            prompt_template = f.read()
            
        prompt = prompt_template.replace("{context}", context).replace("{query}", query)
        return await self._call_llm(prompt)
        
    async def generate_profile(self, user_id: str, display_name: str) -> str:
        context = self.compile_context(days=3, user_id=user_id)
        with open("prompts/person_profile.txt", "r") as f:
            prompt_template = f.read()
            
        prompt = prompt_template.replace("{context}", context).replace("{user_name}", display_name)
        return await self._call_llm(prompt)

    async def delivery_check(self, module_id: str, target_date: str) -> str:
        # Get module details
        mod_res = supabase.table("modules").select("*").eq("id", module_id).execute()
        if not mod_res.data:
            return "Module not found."
        mod = mod_res.data[0]
        
        # Get tasks
        tasks_res = supabase.table("tasks").select("*").eq("module_id", module_id).execute()
        total = len(tasks_res.data) if tasks_res.data else 0
        done = len([t for t in (tasks_res.data or []) if t["status"] == "done"])
        blocked = len([t for t in (tasks_res.data or []) if t["status"] == "blocked"])
        
        metrics = f"Total Tasks: {total}\nCompleted: {done}\nBlocked: {blocked}"
        
        context = self.compile_context(days=7, module_id=module_id)
        
        with open("prompts/delivery_prediction.txt", "r") as f:
            prompt_template = f.read()
            
        prompt = prompt_template.replace("{context}", context).replace("{module_name}", mod["name"]).replace("{target_date}", target_date).replace("{metrics}", metrics)
        return await self._call_llm(prompt)

    async def weekly_narrative(self) -> str:
        context = self.compile_context(days=7)
        with open("prompts/weekly_narrative.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("{context}", context)
        return await self._call_llm(prompt)

    async def generate_weekly_snapshot(self) -> str:
        context = self.compile_context(days=7)
        with open("prompts/weekly_snapshot.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("{context}", context)
        
        summary = await self._call_llm(prompt)
        
        now_utc = datetime.now(timezone.utc)
        start_utc = now_utc - timedelta(days=7)
        supabase.table("jarvis_snapshots").insert({
            "period_start": start_utc.isoformat(),
            "period_end": now_utc.isoformat(),
            "summary": summary
        }).execute()
        return summary

    async def is_quietly_struggling(self, description: str):
        with open("prompts/struggle_check.txt", "r") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("{description}", description)
        
        response = await self._call_llm(prompt)
        if response and response.startswith("YES"):
            reason = response.split("|")[1] if "|" in response else "Possible struggle detected."
            return True, reason
        return False, ""

jarvis_ai = JarvisAI()
