import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

DEBUG = True
