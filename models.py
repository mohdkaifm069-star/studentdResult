
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


# User Account Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


# Student Result Model
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=False)
    mother_name = Column(String(100), nullable=False)
    school_name = Column(String(200), nullable=False)
    district = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)

    subjects = relationship(
        "SubjectMark",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# Subject Marks Model
class SubjectMark(Base):
    __tablename__ = "subject_marks"

    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(100), nullable=False)
    marks = Column(Integer, nullable=False)
    total_marks = Column(Integer, nullable=False, default=100)

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    student = relationship(
        "Student",
        back_populates="subjects"
    )
