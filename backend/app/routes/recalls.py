import httpx
from fastapi import APIRouter, HTTPException

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

    return {
        "total_fetched": len(all_recalls),
        "cfia_food_recalls": len(cfia_recalls),
        "recalls": cfia_recalls
    }