import os
import secrets
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
from app.database import engine
from app.email_service import send_confirmation_email
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

BASE_URL = os.getenv("BASE_URL")

class SubscribeRequest(BaseModel):
    email: str
    categories: List[str]

@router.post("/subscribe")
def subscribe(req: SubscribeRequest):
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id, is_confirmed FROM users WHERE email = :email"),
            {"email": req.email}
        ).fetchone()

        if existing:
            if existing[1]:
                raise HTTPException(status_code=400, detail="Email already subscribed.")
            else:
                raise HTTPException(status_code=400, detail="Check your email to confirm your subscription.")

        token = secrets.token_urlsafe(32)

        conn.execute(text("""
            INSERT INTO users (email, categories, is_confirmed, confirmation_token)
            VALUES (:email, :categories, FALSE, :token)
        """), {
            "email": req.email,
            "categories": req.categories,
            "token": token
        })
        conn.commit()

    confirm_url = f"{BASE_URL}/confirm?token={token}"
    send_confirmation_email(req.email, confirm_url)

    return {"message": "Confirmation email sent. Please check your inbox."}


@router.get("/confirm")
def confirm_email(token: str):
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id FROM users WHERE confirmation_token = :token"),
            {"token": token}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired confirmation token.")

        conn.execute(text("""
            UPDATE users
            SET is_confirmed = TRUE, confirmation_token = NULL
            WHERE confirmation_token = :token
        """), {"token": token})
        conn.commit()

    return {"message": "Email confirmed. You are now subscribed to food recall alerts."}


@router.get("/categories/counts")
def category_counts():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT food_category, COUNT(*) as count
            FROM recalls
            WHERE created_at >= NOW() - INTERVAL '30 days'
            AND food_category IS NOT NULL
            GROUP BY food_category
            ORDER BY count DESC
        """)).fetchall()

    return {
        "category_counts": {row[0]: row[1] for row in rows}
    }