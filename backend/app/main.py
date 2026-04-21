from fastapi import FastAPI
from app.routes.recalls import router
from app.database import create_tables

app = FastAPI()

create_tables()

app.include_router(router)