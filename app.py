# app.py - FIXED VERSION WITH PROPER SESSION MANAGEMENT
from fastapi import FastAPI, Request, Form, UploadFile, Depends, HTTPException, status
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates
from werkzeug.utils import secure_filename
from urllib.parse import quote as url_quote
import os
from datetime import datetime
import logging
from ipfs_client import IPFSClient
from blockchain import Blockchain
from pydantic_settings import BaseSettings
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from database import db_manager, get_db
from database import User, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import traceback


class Settings(BaseSettings):
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random secret key
    TEMPLATES_AUTO_RELOAD: bool = True
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        env_file_encoding = "utf-8"


settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ✅ Enhanced session security with strict settings
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,
    path="/",
)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ✅ Dependency to check if user is authenticated
async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User | None:
    """Get current user if authenticated, otherwise return None"""
    user_email = request.session.get("user")
    authenticated = request.session.get("authenticated", False)

    if not user_email or not authenticated:
        return None

    try:
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()

        if not user:
            # Clear invalid session
            request.session.clear()
            return None

        return user
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        request.session.clear()
        return None


async def get_current_user_required(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user or raise 401"""
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


@app.get("/google-login")
async def google_login(request: Request):
    """Initiate Google OAuth flow"""
    redirect_uri = settings.GOOGLE_REDIRECT_URI.strip()
    logger.info(f"Redirecting to Google OAuth with redirect URI: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth")
async def auth(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        logger.info("Processing OAuth callback")
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await oauth.google.parse_id_token(request, token)

        logger.info(f"User info received: {user_info.get('email')}")

        result = await db.execute(
            select(User).where(User.google_id == user_info["sub"])
        )
        user = result.scalar_one_or_none()

        if user:
            logger.info(f"Existing user logged in: {user.email}")
        else:
            user = User(
                google_id=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name", ""),
                profile_pic=user_info.get("picture", ""),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user created: {user.email}")

        # ✅ Set session with authentication flag
        request.session.clear()  # Clear any old session data
        request.session["user"] = user.email
        request.session["authenticated"] = True
        request.session["login_time"] = datetime.now().isoformat()

        logger.info(f"✅ User authenticated successfully: {user.email}")

        return RedirectResponse(url="/", status_code=302)

    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        traceback.print_exc()
        return RedirectResponse(url="/login?error=auth_failed", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    """Clear session and logout user"""
    user_email = request.session.get("user")
    request.session.clear()
    logger.info(f"User logged out: {user_email}")
    return RedirectResponse(url="/login", status_code=302)


@app.on_event("startup")
async def startup_db_client():
    """Initialize PostgreSQL connection on startup"""
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not set in environment variables!")
        raise ValueError("DATABASE_URL environment variable is required")
    logger.info("Connecting to database...")
    await db_manager.connect(settings.DATABASE_URL)
    logger.info("✅ Database connected successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close PostgreSQL connection on shutdown"""
    await db_manager.close()


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def timestamp_to_string(dt_object: datetime) -> str:
    """Convert a datetime object to a human-readable string."""
    return dt_object.strftime("%Y-%m-%d %H:%M:%S")


ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "doc",
    "docx",
    "zip",
    "mp4",
    "mp3",
}

os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

ipfs_client = IPFSClient()
blockchain = Blockchain()

templates = Jinja2Templates(directory="templates")
templates.env.filters["timestamp_to_string"] = timestamp_to_string


@app.exception_handler(413)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle file too large errors"""
    return JSONResponse(
        status_code=413,
        content={
            "message": f"File too large (max {settings.MAX_CONTENT_LENGTH / (1024 * 1024):.0f}MB)"
        },
    )


# ✅ FIXED: Root route with proper authentication check
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: AsyncSession = Depends(get_db)):
    """Root route - requires authentication"""
    user = await get_current_user_optional(request, db)

    if not user:
        logger.info(
            "❌ Unauthenticated access to root - clearing session and redirecting to login"
        )
        request.session.clear()  # Ensure session is cleared if not authenticated
        return RedirectResponse(url="/login", status_code=302)

    logger.info(f"✅ Authenticated user accessing root: {user.email}")
    return await show_index(request, user, db)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Display login page"""
    user = await get_current_user_optional(request, db)

    if user and not request.query_params.get(
        "code"
    ):  # Only redirect if not an OAuth callback
        logger.info(f"User already authenticated: {user.email}, redirecting to /")
        request.session.clear()  # Clear the session to force re-authentication
        return RedirectResponse(url="/", status_code=302)

    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )


@app.get("/index", response_class=HTMLResponse)
async def index_redirect(request: Request):
    """Redirect /index to root"""
    return RedirectResponse(url="/", status_code=302)


async def show_index(request: Request, user: User, db: AsyncSession):
    """Display main page with user's files"""

    # Get only user's files from the database
    files_result = await db.execute(select(File).where(File.owner_email == user.email))
    user_files = files_result.scalars().all()

    logger.info(f"📊 Displaying {len(user_files)} files for user {user.email}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "chain": user_files,
            "current_user": user,
        },
    )


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = Form(...),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Handle file upload to IPFS and add to blockchain"""
    if not file:
        logger.warning("No file part in request")
        return JSONResponse(status_code=400, content={"message": "No file part"})

    if file.filename == "":
        logger.warning("No file selected")
        return JSONResponse(status_code=400, content={"message": "No selected file"})

    filename = secure_filename(file.filename)
    if not filename or ".." in filename or filename.startswith("/"):
        logger.warning(f"Invalid filename attempted: {filename}")
        return JSONResponse(status_code=400, content={"message": "Invalid filename"})

    if not allowed_file(filename):
        logger.warning(f"File type not allowed: {filename}")
        return JSONResponse(
            status_code=400,
            content={
                "message": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            },
        )

    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"📁 File saved temporarily: {filename}")

        # Check if a file with the same name already exists for the current user
        existing_file = await db.execute(
            select(File).where(
                (File.filename == filename) & (File.owner_email == current_user.email)
            )
        )
        if existing_file.scalar_one_or_none():
            logger.warning(
                f"User {current_user.email} already owns a file named {filename}"
            )
            return JSONResponse(
                status_code=409,
                content={
                    "message": f"You already own a file named '{filename}'. Please rename your file or upload a different one."
                },
            )

        ipfs_hash = ipfs_client.upload_file(file_path)
        logger.info(f"☁️ File uploaded to IPFS: {filename}, CID: {ipfs_hash}")

        new_block = blockchain.create_block(filename, ipfs_hash)
        blockchain.save_to_file()
        logger.info(f"⛓️ Block #{new_block.index} added to blockchain")

        file_data = File(
            filename=filename, ipfs_hash=ipfs_hash, owner_email=current_user.email
        )
        logger.info(f"Attempting to add file_data to database: {file_data.filename}")
        db.add(file_data)
        await db.commit()
        await db.refresh(
            file_data
        )  # Refresh to get any database-generated defaults like id, uploaded_at
        logger.info(
            f"Successfully added file {file_data.filename} with ID {file_data.id} to database."
        )

        logger.info(f"✅ File upload complete for user {current_user.email}")

        return JSONResponse(
            status_code=200,
            content={
                "message": f"File uploaded successfully! IPFS CID: {ipfs_hash}",
                "ipfs_hash": ipfs_hash,
            },
        )

    except Exception as e:
        logger.error(f"❌ Error uploading file: {str(e)}")
        traceback.print_exc()
        await db.rollback()
        return JSONResponse(
            status_code=500, content={"message": f"Error uploading file: {str(e)}"}
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Temporary file cleaned up: {filename}")


@app.get("/download")
async def download_file(
    ipfs_hash: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Fetches a file from IPFS and displays it in the browser."""
    try:
        result = await db.execute(select(File).where(File.ipfs_hash == ipfs_hash))
        records = result.scalars().all()

        if not records:
            raise HTTPException(status_code=404, detail="File not found")

        if len(records) > 1:
            logger.warning(
                "Multiple DB records found for ipfs_hash %s — using the first record. Consider enforcing uniqueness or cleaning duplicates.",
                ipfs_hash,
            )

        file_record = records[0]

        filename = file_record.filename
        file_content = ipfs_client.download_file(ipfs_hash)

        if file_content is None:
            raise HTTPException(status_code=404, detail="File not found on IPFS")

        # Determine content type based on file extension. Include a sensible
        # default and expand common renderable types so the browser can display
        # them inline (open in new tab) instead of forcing a download.
        file_ext = filename.lower().split(".")[-1] if "." in filename else ""
        content_types = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "txt": "text/plain",
            "html": "text/html",
            "htm": "text/html",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "zip": "application/zip",
        }

        content_type = content_types.get(file_ext, "application/octet-stream")

        # Decide whether to request inline display or attachment download.
        # Browsers will render inline for images, pdf, text, html, audio and video
        # when Content-Disposition is 'inline' and a supported media type is sent.
        inline_types = (
            "application/pdf",
            "text/plain",
            "text/html",
        )

        disposition = "attachment"
        if (
            content_type.startswith("image/")
            or content_type.startswith("video/")
            or content_type.startswith("audio/")
            or content_type in inline_types
        ):
            disposition = "inline"

        safe_name = secure_filename(filename) or f"file.{file_ext}"
        encoded_name = url_quote(filename)

        content_disposition = (
            f"{disposition}; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}"
        )

        headers = {"Content-Disposition": content_disposition}

        logger.info(
            f"✅ Serving file {filename} ({ipfs_hash}) as {content_type} with disposition={disposition}"
        )

        return StreamingResponse(
            content=iter([file_content]), media_type=content_type, headers=headers
        )

    except Exception as e:
        logger.error(f"❌ Error serving file {ipfs_hash}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


@app.get("/validate")
async def validate_blockchain(current_user: User = Depends(get_current_user_required)):
    """Validate blockchain integrity"""
    is_valid = blockchain.is_valid()
    if is_valid:
        logger.info("✅ Blockchain validation: VALID")
        return JSONResponse(
            status_code=200,
            content={"status": "valid", "message": "Blockchain is valid"},
        )
    else:
        logger.warning("❌ Blockchain validation: INVALID")
        return JSONResponse(
            status_code=400,
            content={
                "status": "invalid",
                "message": "Blockchain has been tampered with!",
            },
        )


# ✅ Session management endpoint
@app.get("/api/session-status")
async def session_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check current session status"""
    user = await get_current_user_optional(request, db)

    if user:
        return JSONResponse(
            status_code=200,
            content={
                "authenticated": True,
                "user": user.email,
                "name": user.name,
            },
        )
    else:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False},
        )
