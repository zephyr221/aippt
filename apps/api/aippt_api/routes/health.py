from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse


router = APIRouter()


@router.get("/")
def root(request: Request) -> RedirectResponse:
    root_path = request.scope.get("root_path", "").rstrip("/")
    return RedirectResponse(url=f"{root_path}/docs")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
