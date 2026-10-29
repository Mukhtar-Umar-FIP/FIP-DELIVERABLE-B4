# Student Results API - FIP Deliverable B4
# Run with:  uvicorn main:app --reload

import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models import (
    Assessment, AssessmentCreate,
    ResultItem,
    Score, ScoreCreate, ScoreUpdate,
    Student, StudentAverage, StudentCreate, StudentResults,
    Subject, SubjectAverage, SubjectCreate,
)

app = FastAPI(
    title="Student Results API",
    description="Manage subjects, assessments and student scores.",
    version="1.0.0",
)

security = HTTPBasic()

# ------------------------------------------------------------------
# "Database" - just Python dicts kept in memory.
# Everything resets when the server restarts.
# ------------------------------------------------------------------

# the teacher account is fixed, students get added through POST /students
teacher = {"username": "teacher", "password": "teacher123"}

subjects = {}       # id -> Subject
assessments = {}    # id -> Assessment
students = {}       # student_id -> {"full_name": ..., "password": ...}
scores = {}         # id -> Score

next_subject_id = 1
next_assessment_id = 1
next_score_id = 1


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Checks the username/password and returns who is logged in."""
    username = credentials.username
    password = credentials.password

    # compare_digest avoids timing attacks when checking passwords
    if secrets.compare_digest(username, teacher["username"]) and \
       secrets.compare_digest(password, teacher["password"]):
        return {"username": username, "role": "teacher"}

    student = students.get(username)
    if student and secrets.compare_digest(password, student["password"]):
        return {"username": username, "role": "student"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )


def teacher_only(user=Depends(get_current_user)):
    if user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the teacher can do this",
        )
    return user


def can_view_student(student_id, user):
    """A teacher can see everyone. A student can only see their own results."""
    if user["role"] == "student" and user["username"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own results",
        )


# ------------------------------------------------------------------
# Small helpers
# ------------------------------------------------------------------

def find_student(student_id):
    if student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return students[student_id]


def find_assessment(assessment_id):
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")
    return assessments[assessment_id]


def check_score_range(score, assessment):
    if score > assessment.max_score:
        raise HTTPException(
            status_code=422,
            detail=f"Score {score} is higher than the max score ({assessment.max_score}) for this assessment",
        )


def percent(score, max_score):
    return round(score / max_score * 100, 2)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "Student Results API is running. Go to /docs to try it out."}


# ---------- Subjects ----------

@app.post("/subjects", response_model=Subject, status_code=201)
def add_subject(data: SubjectCreate, user=Depends(teacher_only)):
    global next_subject_id

    for s in subjects.values():
        if s.name == data.name:
            raise HTTPException(status_code=409, detail=f"Subject '{data.name}' already exists")

    subject = Subject(id=next_subject_id, name=data.name)
    subjects[subject.id] = subject
    next_subject_id += 1
    return subject


@app.get("/subjects", response_model=list[Subject])
def list_subjects(user=Depends(get_current_user)):
    return list(subjects.values())


# ---------- Students ----------

@app.post("/students", response_model=Student, status_code=201)
def add_student(data: StudentCreate, user=Depends(teacher_only)):
    if data.student_id in students:
        raise HTTPException(status_code=409, detail=f"Student {data.student_id} already exists")

    students[data.student_id] = {"full_name": data.full_name, "password": data.password}
    # never send the password back
    return Student(student_id=data.student_id, full_name=data.full_name)


@app.get("/students", response_model=list[Student])
def list_students(user=Depends(teacher_only)):
    return [Student(student_id=sid, full_name=s["full_name"]) for sid, s in students.items()]


# ---------- Assessments ----------

@app.post("/assessments", response_model=Assessment, status_code=201)
def add_assessment(data: AssessmentCreate, user=Depends(teacher_only)):
    global next_assessment_id

    if data.subject_id not in subjects:
        raise HTTPException(status_code=404, detail=f"Subject {data.subject_id} not found")

    assessment = Assessment(id=next_assessment_id, **data.model_dump())
    assessments[assessment.id] = assessment
    next_assessment_id += 1
    return assessment


@app.get("/assessments", response_model=list[Assessment])
def list_assessments(user=Depends(get_current_user)):
    return list(assessments.values())


# ---------- Scores ----------

@app.post("/scores", response_model=Score, status_code=201)
def add_score(data: ScoreCreate, user=Depends(teacher_only)):
    global next_score_id

    find_student(data.student_id)
    assessment = find_assessment(data.assessment_id)
    check_score_range(data.score, assessment)

    # one score per student per assessment - use PUT to change it
    for s in scores.values():
        if s.student_id == data.student_id and s.assessment_id == data.assessment_id:
            raise HTTPException(
                status_code=409,
                detail=f"{data.student_id} already has a score for this assessment (score id {s.id}). Use PUT to update it.",
            )

    score = Score(id=next_score_id, **data.model_dump())
    scores[score.id] = score
    next_score_id += 1
    return score


@app.put("/scores/{score_id}", response_model=Score)
def update_score(score_id: int, data: ScoreUpdate, user=Depends(teacher_only)):
    if score_id not in scores:
        raise HTTPException(status_code=404, detail=f"Score {score_id} not found")

    score = scores[score_id]
    check_score_range(data.score, assessments[score.assessment_id])

    score.score = data.score
    return score


# ---------- Results and averages ----------

@app.get("/students/{student_id}/results", response_model=StudentResults)
def get_student_results(student_id: str, user=Depends(get_current_user)):
    can_view_student(student_id, user)
    student = find_student(student_id)

    results = []
    for s in scores.values():
        if s.student_id != student_id:
            continue
        a = assessments[s.assessment_id]
        results.append(ResultItem(
            score_id=s.id,
            subject=subjects[a.subject_id].name,
            assessment=a.title,
            score=s.score,
            max_score=a.max_score,
            percentage=percent(s.score, a.max_score),
        ))

    return StudentResults(student_id=student_id, full_name=student["full_name"], results=results)


@app.get("/students/{student_id}/average", response_model=StudentAverage)
def get_student_average(student_id: str, user=Depends(get_current_user)):
    can_view_student(student_id, user)
    find_student(student_id)

    # group percentages by subject
    by_subject = {}
    for s in scores.values():
        if s.student_id != student_id:
            continue
        a = assessments[s.assessment_id]
        name = subjects[a.subject_id].name
        by_subject.setdefault(name, []).append(percent(s.score, a.max_score))

    if not by_subject:
        raise HTTPException(status_code=404, detail=f"No scores recorded yet for {student_id}")

    subject_averages = [
        SubjectAverage(subject=name, average_percentage=round(sum(p) / len(p), 2))
        for name, p in by_subject.items()
    ]
    overall = round(sum(x.average_percentage for x in subject_averages) / len(subject_averages), 2)

    return StudentAverage(student_id=student_id, overall_average=overall, subjects=subject_averages)


@app.get("/subjects/{subject_id}/average")
def get_subject_average(subject_id: int, user=Depends(teacher_only)):
    """Class average for one subject (teacher only)."""
    if subject_id not in subjects:
        raise HTTPException(status_code=404, detail=f"Subject {subject_id} not found")

    percentages = []
    for s in scores.values():
        a = assessments[s.assessment_id]
        if a.subject_id == subject_id:
            percentages.append(percent(s.score, a.max_score))

    if not percentages:
        raise HTTPException(status_code=404, detail="No scores recorded for this subject yet")

    return {
        "subject": subjects[subject_id].name,
        "number_of_scores": len(percentages),
        "class_average": round(sum(percentages) / len(percentages), 2),
    }
