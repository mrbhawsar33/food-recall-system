import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine
from app.email_service import send_recall_email
from app.ai_service import generate_summary

router = APIRouter()

OPEN_DATA_URL = "https://recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json"


def is_recent(date_str: str) -> bool:
    if not date_str:
        return False
    from datetime import datetime, timedelta
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date >= datetime.now() - timedelta(days=30)
    except:
        return False


def detect_anomalies(conn, nid: str, title: str, recall_class: str) -> dict:
    is_class1 = recall_class == "Class 1"

    first_word = title.lower().split()[0] if title else ""
    recent = conn.execute(text("""
        SELECT COUNT(*) FROM recalls
        WHERE LOWER(title) LIKE :pattern
        AND created_at >= NOW() - INTERVAL '30 days'
        AND nid != :nid
    """), {
        "pattern": f"{first_word}%",
        "nid": nid
    }).scalar()

    is_repeat = recent > 0

    return {
        "is_class1": is_class1,
        "is_repeat_recall": is_repeat
    }


@router.get("/recalls/sync")
async def sync_recalls():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(OPEN_DATA_URL)
            all_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch open data: {str(e)}")

    # filter CFIA only + recent only
    cfia_recalls = [
        r for r in all_data
        if r.get("Organization") == "CFIA"
        and is_recent(r.get("Last updated", ""))
        and r.get("Archived") == "0"
    ]

    new_recalls = []

    with engine.connect() as conn:
        for recall in cfia_recalls:
            nid = recall.get("NID")
            title = recall.get("Title", "")
            recall_class = recall.get("Recall class", "")
            food_category = recall.get("Category", "")
            issue = recall.get("Issue", "")
            last_updated = recall.get("Last updated")
            url = recall.get("URL", "")

            existing = conn.execute(
                text("SELECT id FROM recalls WHERE nid = :nid"),
                {"nid": nid}
            ).fetchone()

            if existing:
                continue

            anomalies = detect_anomalies(conn, nid, title, recall_class)
            if recall_class == "Class 1":
                summary = generate_summary(title, recall_class)
            else:
                severity_text = "moderate risk" if recall_class == "Class 2" else "low risk"
                summary = f"This is a {recall_class} ({severity_text}) recall for {title}. Monitor the situation and follow instructions from the recall notice."

            conn.execute(text("""
                INSERT INTO recalls (
                    recall_id, nid, title, recall_class, food_category,
                    issue, url, last_updated, ai_summary
                )
                VALUES (
                    :recall_id, :nid, :title, :recall_class, :food_category,
                    :issue, :url, :last_updated, :ai_summary
                )
            """), {
                "recall_id": nid,
                "nid": nid,
                "title": title,
                "recall_class": recall_class,
                "food_category": food_category,
                "issue": issue,
                "url": url,
                "last_updated": last_updated,
                "ai_summary": summary
            })

            new_recalls.append({
                "nid": nid,
                "title": title,
                "recall_class": recall_class,
                "food_category": food_category,
                "issue": issue,
                "ai_summary": summary,
                "is_class1": anomalies["is_class1"],
                "is_repeat_recall": anomalies["is_repeat_recall"]
            })

        conn.commit()

    class1_recalls = [r for r in new_recalls if r["is_class1"]]
    lower_recalls = [r for r in new_recalls if not r["is_class1"]]

    if class1_recalls:
        send_recall_email(class1_recalls)
        with engine.connect() as conn:
            for r in class1_recalls:
                conn.execute(text("""
                    UPDATE recalls SET dispatched = TRUE WHERE nid = :nid
                """), {"nid": r["nid"]})
            conn.commit()

    return {
        "new_recalls_found": len(new_recalls),
        "class1_immediately_sent": len(class1_recalls),
        "class2_3_queued_for_digest": len(lower_recalls),
        "recalls": new_recalls
    }


@router.get("/recalls/dashboard")
def get_dashboard_recalls(
    category: str = None,
    severity: str = None,
    search: str = None
):
    filters = ["1=1"]
    params = {}

    if category:
        filters.append("LOWER(food_category) LIKE :category")
        params["category"] = f"%{category.lower()}%"

    if severity:
        filters.append("recall_class = :severity")
        params["severity"] = severity

    if search:
        filters.append("LOWER(title) LIKE :search")
        params["search"] = f"%{search.lower()}%"

    where_clause = " AND ".join(filters)

    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT nid, title, recall_class, food_category, issue,
                   last_updated, ai_summary, created_at
            FROM recalls
            WHERE {where_clause}
            ORDER BY created_at DESC
        """), params).fetchall()

    results = []
    for row in rows:
        results.append({
            "nid": row[0],
            "title": row[1],
            "recall_class": row[2],
            "food_category": row[3],
            "issue": row[4],
            "last_updated": str(row[5]) if row[5] else None,
            "ai_summary": row[6],
            "created_at": str(row[7])
        })

    return {"total": len(results), "recalls": results}


@router.get("/recalls")
async def get_cfia_recalls():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT nid, title, recall_class, food_category, issue, last_updated, ai_summary
            FROM recalls
            ORDER BY created_at DESC
            LIMIT 50
        """)).fetchall()

    results = []
    for row in rows:
        results.append({
            "nid": row[0],
            "title": row[1],
            "recall_class": row[2],
            "food_category": row[3],
            "issue": row[4],
            "last_updated": str(row[5]) if row[5] else None,
            "ai_summary": row[6]
        })

    return {"total": len(results), "recalls": results}

@router.get("/recalls/digest")
def send_digest():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT nid, title, recall_class, food_category, issue, ai_summary
            FROM recalls
            WHERE dispatched = FALSE
            AND recall_class IN ('Class 2', 'Class 3')
            AND created_at >= NOW() - INTERVAL '30 days'
        """)).fetchall()

        if not rows:
            return {"message": "No pending recalls for digest."}

        digest_recalls = []
        for row in rows:
            digest_recalls.append({
                "nid": row[0],
                "title": row[1],
                "recall_class": row[2],
                "food_category": row[3],
                "issue": row[4],
                "ai_summary": row[5],
                "is_class1": False,
                "is_repeat_recall": False
            })

        send_recall_email(digest_recalls)

        for r in digest_recalls:
            conn.execute(text("""
                UPDATE recalls SET dispatched = TRUE WHERE nid = :nid
            """), {"nid": r["nid"]})
        conn.commit()

    return {
        "digest_sent": len(digest_recalls),
        "recalls": digest_recalls
    }