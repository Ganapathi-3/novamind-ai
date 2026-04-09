
import json, shutil, logging
from datetime import timedelta
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import User, ChatHistory
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role, ACCESS_TOKEN_EXPIRE_MINUTES
from rbac import get_allowed_departments, get_role_summary
from rag import answer_question, ingest_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Enterprise AI Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = Path("../data/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "intern"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    role_used: str

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    valid_roles = ["admin", "hr", "employee", "intern"]
    if req.role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Choose from: {valid_roles}")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already taken.")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered.")
    user = User(username=req.username, email=req.email, hashed_password=hash_password(req.password), role=req.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": f"User '{user.username}' registered successfully.", "role": user.role}

@app.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password.", headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, token_type="bearer", username=user.username, role=user.role)

@app.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email, "role": current_user.role, "allowed_departments": get_allowed_departments(current_user.role)}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")
    answer, sources = answer_question(req.question, current_user.role)
    db.add(ChatHistory(user_id=current_user.id, question=req.question, answer=answer, sources=json.dumps(sources)))
    db.commit()
    return AskResponse(answer=answer, sources=sources, role_used=current_user.role)

@app.get("/history")
def get_history(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    return [{"id": r.id, "question": r.question, "answer": r.answer, "sources": json.loads(r.sources) if r.sources else [], "timestamp": str(r.timestamp)} for r in rows]

@app.post("/upload")
async def upload(file: UploadFile = File(...), department: str = Form(...), access_level: str = Form(default="internal"), current_user: User = Depends(require_role("admin"))):
    allowed_ext = {".pdf", ".txt", ".md"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type '{ext}'.")
    dest_dir = UPLOAD_DIR / department.lower()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        count = ingest_document(str(dest), department=department.lower(), access_level=access_level.lower())
        return {"message": f"Ingested '{file.filename}'", "chunks_created": count, "department": department}
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")

@app.get("/admin/users")
def list_users(current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in db.query(User).all()]

@app.patch("/admin/users/{user_id}/role")
def change_role(user_id: int, new_role: str, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    valid = ["admin", "hr", "employee", "intern"]
    if new_role not in valid:
        raise HTTPException(400, f"Invalid role. Choose from: {valid}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    old = user.role
    user.role = new_role
    db.commit()
    return {"message": f"Changed '{user.username}' from '{old}' to '{new_role}'."}

@app.get("/admin/permissions")
def permissions(current_user: User = Depends(require_role("admin"))):
    return get_role_summary()
