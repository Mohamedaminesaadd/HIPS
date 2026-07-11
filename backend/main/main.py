from fastapi import FastAPI
from backend.api.routes.sleep import router as sleep_router

app = FastAPI()

app.include_router(sleep_router)