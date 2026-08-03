# from fastapi import APIRouter, Request, Depends
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from core.auth import get_current_user
# from database.database import User

# router = APIRouter(tags=["Pages"])
# templates = Jinja2Templates(directory="templates")

# @router.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse(request=request, name="login.html")

# @router.get("/", response_class=HTMLResponse)
# async def dashboard(request: Request, user: User = Depends(get_current_user)):
#     if not user:
#         return templates.TemplateResponse(request=request, name="login.html")
#     return templates.TemplateResponse(request=request, name="cameras.html", context={"active_page": "cameras", "user": user})

# @router.get("/models", response_class=HTMLResponse)
# async def view_models(request: Request, user: User = Depends(get_current_user)):
#     if not user:
#         return templates.TemplateResponse(request=request, name="login.html")
#     return templates.TemplateResponse(request=request, name="models.html", context={"active_page": "models", "user": user})

# @router.get("/events", response_class=HTMLResponse)
# async def view_events(request: Request, user: User = Depends(get_current_user)):
#     if not user:
#         return templates.TemplateResponse(request=request, name="login.html")
#     return templates.TemplateResponse(request=request, name="events.html", context={"active_page": "events", "user": user})