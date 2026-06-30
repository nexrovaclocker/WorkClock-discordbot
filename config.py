import os
from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    TOKEN = os.environ.get("TOKEN")
    STATUS_CHANNEL_ID = int(os.environ.get("STATUS_CHANNEL_ID", 0)) if os.environ.get("STATUS_CHANNEL_ID") else 0
    OPS_BRAIN_CHANNEL_ID = int(os.environ.get("OPS_BRAIN_CHANNEL_ID", 0)) if os.environ.get("OPS_BRAIN_CHANNEL_ID") else 0
    STANDUP_CHANNEL_ID = int(os.environ.get("STANDUP_CHANNEL_ID", 0)) if os.environ.get("STANDUP_CHANNEL_ID") else 0
    
    ADMIN_IDS = [x.strip() for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    FOUNDER_IDS = [x.strip() for x in os.environ.get("FOUNDER_IDS", "").split(",") if x.strip()]
    MORNING_BRIEFING_USER_IDS = [x.strip() for x in os.environ.get("MORNING_BRIEFING_USER_IDS", "").split(",") if x.strip()]
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    PORT = int(os.environ.get("PORT", 8080))
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

config = Config()
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY) if config.SUPABASE_URL and config.SUPABASE_KEY else None
