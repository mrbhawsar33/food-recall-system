import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine

router = APIRouter()

HEALTH_CANADA_URL = "https://healthycanadians.gc.ca/recall-alert-rappel-avis/api/recent/en"

@router.get("/recalls")
async def get_cfia_recalls():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(HEALTH_CANADA_URL)
            data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recalls: {str(e)}")

    all_recalls = data.get("results", {}).get("ALL", [])
    cfia_recalls = data.get("results", {}).get("FOOD", [])

    saved = 0
    skipped = 0

    with engine.connect() as conn:
        for recall in cfia_recalls:
            recall_id = recall.get("recallId")
            title = recall.get("title")
            category = recall.get("category", [None])[0]
            date_published = recall.get("date_published")
            url = recall.get("url")

            existing = conn.execute(
                text("SELECT id FROM recalls WHERE recall_id = :rid"),
                {"rid": recall_id}
            ).fetchone()

            if existing:
                skipped += 1
            else:
                conn.execute(text("""
                    INSERT INTO recalls (recall_id, title, category, date_published, url)
                    VALUES (:recall_id, :title, :category, :date_published, :url)
                """), {
                    "recall_id": recall_id,
                    "title": title,
                    "category": category,
                    "date_published": date_published,
                    "url": url
                })
                saved += 1

        conn.commit()

    return {
        "total_fetched": len(all_recalls),
        "cfia_food_recalls": len(cfia_recalls),
        "saved_to_db": saved,
        "skipped_duplicates": skipped
    }