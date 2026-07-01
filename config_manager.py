from config import supabase, config

class ConfigManager:
    def __init__(self):
        self._cache = None

    def get_settings(self):
        """Fetch settings from Supabase, or return defaults if missing."""
        if self._cache:
            return self._cache
            
        try:
            res = supabase.table("bot_settings").select("*").eq("id", 1).execute()
            if res.data:
                self._cache = res.data[0]
                return self._cache
        except Exception as e:
            print(f"Error fetching bot_settings: {e}")
            
        # Fallback to .env defaults if table is empty or error
        default_settings = {
            "id": 1,
            "admin_ids": ",".join(config.ADMIN_IDS),
            "founder_ids": ",".join(config.FOUNDER_IDS),
            "daily_dm_time": "22:00"
        }
        
        try:
            supabase.table("bot_settings").upsert(default_settings).execute()
        except Exception:
            pass
            
        self._cache = default_settings
        return default_settings

    def update_settings(self, updates: dict):
        """Update settings in Supabase and refresh cache."""
        try:
            updates["id"] = 1
            res = supabase.table("bot_settings").upsert(updates).execute()
            if res.data:
                self._cache = res.data[0]
                return True
        except Exception as e:
            print(f"Error updating bot_settings: {e}")
            return False
        return False

    def is_admin(self, user_id: str) -> bool:
        settings = self.get_settings()
        admin_ids = [x.strip() for x in settings.get("admin_ids", "").split(",") if x.strip()]
        return str(user_id) in admin_ids or self.is_founder(user_id)

    def is_founder(self, user_id: str) -> bool:
        settings = self.get_settings()
        founder_ids = [x.strip() for x in settings.get("founder_ids", "").split(",") if x.strip()]
        return str(user_id) in founder_ids

bot_config = ConfigManager()
