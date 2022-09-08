import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ['TOKEN']
WORKERS_KV_ACCOUNT = os.environ['WORKERS_KV_ACCOUNT']
WORKERS_KV_NAMESPACE = os.environ['WORKERS_KV_NAMESPACE']
WORKERS_KV_NAMESPACE = os.environ['WORKERS_KV_NAMESPACE_G']
CF_API_KEY = os.environ['CF_API_KEY']
