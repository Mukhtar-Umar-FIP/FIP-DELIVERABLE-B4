# Pydantic models used to validate what comes into the API
# and to shape what goes back out.

from pydantic import BaseModel, Field, field_validator


# ---------- Subjects ----------

class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, examples=["Mathematics"])

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("subject name cannot be blank")
        return value.title()


class Subject(SubjectCreate):
    id: int


# ---------- Students ----------

class StudentCreate(BaseModel):
    # student ids look like STU001, STU002 ...
    student_id: str = Field(..., pattern=r"^STU\d{3}$", examples=["STU001"])
    full_name: str = Field(..., min_length=3, max_length=80, examples=["Aisha Bello"])
    password: str = Field(..., min_length=6, examples=["aisha123"])


class Student(BaseModel):
    student_id: str
    full_name: str


# ---------- Assessments ----------

class AssessmentCreate(BaseModel):
    subject_id: int = Field(..., gt=0, examples=[1])
    title: str = Field(..., min_length=2, max_length=50, examples=["First Test"])
    max_score: float = Field(..., gt=0, le=100, examples=[20])


class Assessment(AssessmentCreate):
    id: int


# ---------- Scores ----------

class ScoreCreate(BaseModel):
    student_id: str = Field(..., pattern=r"^STU\d{3}$", examples=["STU001"])
    assessment_id: int = Field(..., gt=0, examples=[1])
    score: float = Field(..., ge=0, examples=[15])


class ScoreUpdate(BaseModel):
    score: float = Field(..., ge=0, examples=[18])


class Score(BaseModel):
    id: int
    student_id: str
    assessment_id: int
    score: float


# ---------- Results / averages ----------

class ResultItem(BaseModel):
    score_id: int
    subject: str
    assessment: str
    score: float
    max_score: float
    percentage: float


class StudentResults(BaseModel):
    student_id: str
    full_name: str
    results: list[ResultItem]


class SubjectAverage(BaseModel):
    subject: str
    average_percentage: float


class StudentAverage(BaseModel):
    student_id: str
    overall_average: float
    subjects: list[SubjectAverage]
