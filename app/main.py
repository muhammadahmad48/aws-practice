from fastapi import FastAPI
from app.core.secrets_manager import settings

app = FastAPI(title="Lumaya Backend", version="1.0.0")

# app.include_router(api_router, prefix="/api")

print('=================settings=======================',settings)