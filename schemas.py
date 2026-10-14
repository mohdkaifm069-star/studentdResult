
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Create Account
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# User Response
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# JWT Login Response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Subject Result
class SubjectResponse(BaseModel):
    subject_name: str
    marks: int
    total_marks: int
    status: str


# Student Result
class StudentResultResponse(BaseModel):
    roll_no: int
    name: str
    father_name: str
    mother_name: str
    school_name: str
    district: str
    academic_year: str

    subjects: list[SubjectResponse]
    total_obtained: int
    total_marks: int
    percentage: float
    result: str

    model_config = ConfigDict(from_attributes=True)


