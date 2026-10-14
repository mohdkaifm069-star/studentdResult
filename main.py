
from datetime import datetime, timedelta, timezone
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash
from jose import jwt, JWTError

from database import get_db, Base, engine
from models import User, Student
from schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    StudentResultResponse,
)


# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Student Result Checker API")


# CORS settings for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# Password hashing
password_hash = PasswordHash.recommended()


# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is missing. "
        "Set SECRET_KEY before starting the application."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bearer_scheme = HTTPBearer()


# Create JWT token
def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Verify JWT token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


@app.get("/")
def home():
    return {"message": "Student Result API is running"}


# REGISTER
@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    email = str(user_data.email).lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    hashed_password = password_hash.hash(user_data.password)

    new_user = User(
        name=user_data.name.strip(),
        email=email,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    return new_user


# LOGIN
@app.post(
    "/auth/login",
    response_model=TokenResponse
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    email = str(login_data.email).lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None or not password_hash.verify(
        login_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# CHECK STUDENT RESULT - LOGIN REQUIRED
@app.get(
    "/result/{roll_no}",
    response_model=StudentResultResponse
)
def check_result(
    roll_no: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = (
        db.query(Student)
        .options(selectinload(Student.subjects))
        .filter(Student.roll_no == roll_no)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student result not found"
        )

    if not student.subjects:
        raise HTTPException(
            status_code=404,
            detail="No subjects found for this student"
        )

    subject_results = []
    total_obtained = 0
    total_marks = 0
    failed_subjects = 0

    for subject in student.subjects:
        status = "PASS" if subject.marks >= 33 else "FAIL"

        if status == "FAIL":
            failed_subjects += 1

        total_obtained += subject.marks
        total_marks += subject.total_marks

        subject_results.append({
            "subject_name": subject.subject_name,
            "marks": subject.marks,
            "total_marks": subject.total_marks,
            "status": status
        })

    percentage = (
        round(total_obtained / total_marks * 100, 2)
        if total_marks > 0
        else 0.0
    )

    overall_result = "FAIL" if failed_subjects >= 3 else "PASS"

    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "school_name": student.school_name,
        "district": student.district,
        "academic_year": student.academic_year,
        "subjects": subject_results,
        "total_obtained": total_obtained,
        "total_marks": total_marks,
        "percentage": percentage,
        "result": overall_result
    }
