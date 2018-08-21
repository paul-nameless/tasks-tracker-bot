import os

REDIS_URI = 'redis://127.0.0.1:6379/0'
API_TOKEN = None

# override locals with env variables
for k, v in os.environ.items():
    if k in locals():
        locals()[k] = v
