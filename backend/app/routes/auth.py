from fastapi import APIRouter

router = APIRouter()


@router.get("/login")
async def login():
    """Redirect user to OAuth provider. Implemented in Phase 1 OAuth step."""
    return {"detail": "OAuth login not yet implemented"}


@router.get("/callback")
async def callback():
    """Handle OAuth provider callback. Implemented in Phase 1 OAuth step."""
    return {"detail": "OAuth callback not yet implemented"}


@router.post("/logout")
async def logout():
    """Invalidate session. Implemented in Phase 1 OAuth step."""
    return {"detail": "Logout not yet implemented"}
