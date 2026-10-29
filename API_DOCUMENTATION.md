# API Documentation

Base URL: `http://127.0.0.1:8000`

Auth: **HTTP Basic** on every endpoint except `GET /`.
Teacher login: `teacher` / `teacher123`. Students log in with their student ID and password.

FastAPI also generates interactive docs at `/docs` (Swagger) and `/redoc`.

---

## Health check

### `GET /`
No login needed.

**Response 200**
```json
{ "message": "Student Results API is running. Go to /docs to try it out." }
```

---

## Subjects

### `POST /subjects` (teacher)

| Field | Type | Rules |
|---|---|---|
| name | string | 2–50 characters, saved in Title Case |

**Request**
```json
{ "name": "Mathematics" }
```
**Response 201**
```json
{ "name": "Mathematics", "id": 1 }
```
**Errors:** 401, 403, 409 (subject already exists), 422 (bad name)

### `GET /subjects` (logged in)
Returns a list of all subjects.

### `GET /subjects/{subject_id}/average` (teacher)
Class average for one subject.

**Response 200**
```json
{ "subject": "Mathematics", "number_of_scores": 3, "class_average": 76.67 }
```
**Errors:** 401, 403, 404 (subject not found / no scores yet)

---

## Students

### `POST /students` (teacher)

| Field | Type | Rules |
|---|---|---|
| student_id | string | must match `STU` + 3 digits, e.g. `STU001` |
| full_name | string | 3–80 characters |
| password | string | at least 6 characters (used by the student to log in) |

**Request**
```json
{ "student_id": "STU001", "full_name": "Aisha Bello", "password": "aisha123" }
```
**Response 201** (password is not returned)
```json
{ "student_id": "STU001", "full_name": "Aisha Bello" }
```
**Errors:** 401, 403, 409 (student already exists), 422

### `GET /students` (teacher)
Returns a list of all students (ID and name only).

---

## Assessments

### `POST /assessments` (teacher)

| Field | Type | Rules |
|---|---|---|
| subject_id | int | must be an existing subject |
| title | string | 2–50 characters |
| max_score | number | more than 0, at most 100 |

**Request**
```json
{ "subject_id": 1, "title": "First Test", "max_score": 20 }
```
**Response 201**
```json
{ "subject_id": 1, "title": "First Test", "max_score": 20.0, "id": 1 }
```
**Errors:** 401, 403, 404 (subject not found), 422

### `GET /assessments` (logged in)
Returns a list of all assessments.

---

## Scores

### `POST /scores` (teacher), add a score

| Field | Type | Rules |
|---|---|---|
| student_id | string | existing student, format `STU001` |
| assessment_id | int | existing assessment |
| score | number | 0 up to the assessment's max_score |

**Request**
```json
{ "student_id": "STU001", "assessment_id": 1, "score": 15 }
```
**Response 201**
```json
{ "id": 1, "student_id": "STU001", "assessment_id": 1, "score": 15.0 }
```
**Errors:**
- 404: student or assessment not found
- 409: student already has a score for this assessment
- 422: score is negative or higher than max_score

### `PUT /scores/{score_id}` (teacher), update a result

**Request**
```json
{ "score": 18 }
```
**Response 200**
```json
{ "id": 1, "student_id": "STU001", "assessment_id": 1, "score": 18.0 }
```
**Errors:** 401, 403, 404 (score not found), 422 (score out of range)

---

## Results

### `GET /students/{student_id}/results` (teacher, or the student themselves)

**Response 200**
```json
{
  "student_id": "STU001",
  "full_name": "Aisha Bello",
  "results": [
    { "score_id": 1, "subject": "Mathematics", "assessment": "First Test", "score": 18.0, "max_score": 20.0, "percentage": 90.0 },
    { "score_id": 2, "subject": "Mathematics", "assessment": "Exam", "score": 48.0, "max_score": 60.0, "percentage": 80.0 },
    { "score_id": 3, "subject": "English", "assessment": "First Test", "score": 14.0, "max_score": 20.0, "percentage": 70.0 }
  ]
}
```
**Errors:** 401, 403 (a student looking at someone else), 404 (student not found)

### `GET /students/{student_id}/average` (teacher, or the student themselves)

**Response 200**
```json
{
  "student_id": "STU001",
  "overall_average": 77.5,
  "subjects": [
    { "subject": "Mathematics", "average_percentage": 85.0 },
    { "subject": "English", "average_percentage": 70.0 }
  ]
}
```
**Errors:** 401, 403, 404 (student not found / no scores yet)

---

## Error format

Errors raised by the app look like this:
```json
{ "detail": "Student STU009 not found" }
```

Errors from Pydantic validation (wrong type, missing field, out of range) list each problem:
```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "score"],
      "msg": "Input should be greater than or equal to 0",
      "input": -5,
      "ctx": { "ge": 0.0 }
    }
  ]
}
```

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 401 | Not logged in / wrong password |
| 403 | Logged in but not allowed |
| 404 | Not found |
| 409 | Already exists (duplicate) |
| 422 | Data is not valid |
