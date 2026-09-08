from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.places import PlaceSearchResponse, PlaceResolveRequest, PlaceResolveResponse
from app.services.place_service import PlaceService

router = APIRouter(prefix="/places", tags=["Places"])


@router.get("/search", response_model=PlaceSearchResponse)
async def search_places(q: str = Query(..., min_length=2, description="City or place search query")):
    """Search for cities in the offline database."""
    results = PlaceService.search(q)
    return PlaceSearchResponse(success=True, count=len(results), results=results)


@router.post("/resolve", response_model=PlaceResolveResponse)
async def resolve_place(body: PlaceResolveRequest):
    """Resolve a place name to coordinates and timezone."""
    item = PlaceService.resolve(body.place_name)
    return PlaceResolveResponse(success=True, found=item is not None, place=item)
