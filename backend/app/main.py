from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.recalls import router as recalls_router
from app.routes.users import router as users_router
from app.database import create_tables

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(recalls_router)
app.include_router(users_router)