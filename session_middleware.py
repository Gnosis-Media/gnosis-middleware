# session_middleware.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import requests
import time
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "http://127.0.0.1"
PORT = 5000

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request URL: {request.url}")
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"Response status: {response.status_code} | Time: {process_time:.4f}s")
    return response

# Middleware for checking login status
@app.middleware("http")
async def check_login(request: Request, call_next):
    if request.url.path not in ["/login", "/"]:
        user_id = request.cookies.get("user_id")
        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        # Optionally check if session is still valid based on expiration timestamp
        session_expiration = request.cookies.get("session_expiration")
        if not session_expiration or time.time() > float(session_expiration):
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("user_id")
            response.delete_cookie("session_expiration")
            return response

    response = await call_next(request)
    return response

# Login route that interacts with Flask app (assuming it's running locally for simplicity)
@app.post("/login")
async def login(request: Request):
    data = await request.form()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Missing username or password")

    # Call the existing user API to authenticate the user
    response = requests.post(f"{URL}:{PORT}/api/login", json={"username": username, "password": password})
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data.get("user_id")  # assuming the Flask app returns user_id
        expiration_time = time.time() + 3600  # session expires in 1 hour

        redirect_response = RedirectResponse(url="/login", status_code=302)
        redirect_response.set_cookie(key="user_id", value=user_id)
        redirect_response.set_cookie(key="session_expiration", value=str(expiration_time))
        return redirect_response
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

# Logout route to clear session cookies
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    response.delete_cookie("session_expiration")
    return response

# Mypage.. not yet implemented

# @app.get("/mypage")
# async def mypage(request: Request):
#     user_id = request.cookies.get("user_id")
#     if user_id:
#         # You may call the user API to fetch user details if needed
#         response = requests.get(f"{URL}:{PORT}/api/users/{user_id}")
#         if response.status_code == 200:
#             user_data = response.json()
#             return {"message": "Welcome to your page", "user": user_data}
#     raise HTTPException(status_code=403, detail="Not authorized")
