# Student Results API (FIP Deliverable B4)

A small FastAPI project for keeping track of subjects, assessments and student scores.
A teacher can add subjects, assessments and scores, update a result, and check averages.
Students can log in and see only their own results.

Data is kept in memory (Python dictionaries), so it resets every time the server restarts.
I kept it like this so the project stays simple. A real school system would use a database.

## What's in the repo

| File / Folder | What it is |
|---|---|
| `main.py` | The FastAPI app with all the endpoints and the login check |
| `models.py` | Pydantic models that validate the request data |
| `requirements.txt` | Packages needed |
| `API_DOCUMENTATION.md` | List of all endpoints, what they need and what they return |
| `samples/` | Sample JSON requests and responses |
| `postman/Student_Results_API.postman_collection.json` | Postman collection for testing |

## How to run it

```bash
# 1. clone the repo
git clone https://github.com/Mukhtar-Umar-FIP/FIP-DELIVERABLE-B4.git
cd FIP-DELIVERABLE-B4

# 2. (optional) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux

# 3. install packages
pip install -r requirements.txt

# 4. start the server
uvicorn main:app --reload
```

The API runs on `http://127.0.0.1:8000`.
Open `http://127.0.0.1:8000/docs` to see and test every endpoint in the browser (click **Authorize** and log in first).

## Login details

The API uses **HTTP Basic Authentication**.

| Role | Username | Password |
|---|---|---|
| Teacher | `teacher` | `teacher123` |
| Student | their student ID, e.g. `STU001` | the password the teacher set when adding them |

- **Teacher**: can do everything.
- **Student**: can only view their own results and average.

## Endpoints (quick list)

| Method | Endpoint | Who can use it | What it does |
|---|---|---|---|
| GET | `/` | anyone | Check the API is running |
| POST | `/subjects` | teacher | Add a subject |
| GET | `/subjects` | logged in | List subjects |
| POST | `/students` | teacher | Add a student |
| GET | `/students` | teacher | List students |
| POST | `/assessments` | teacher | Add an assessment (test, exam, etc.) to a subject |
| GET | `/assessments` | logged in | List assessments |
| POST | `/scores` | teacher | Add a student's score |
| PUT | `/scores/{score_id}` | teacher | Update a score |
| GET | `/students/{student_id}/results` | teacher or that student | Get a student's results |
| GET | `/students/{student_id}/average` | teacher or that student | Get a student's averages |
| GET | `/subjects/{subject_id}/average` | teacher | Class average for a subject |

Full details are in [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Testing with Postman

1. Open Postman, click **Import**, and pick `postman/Student_Results_API.postman_collection.json`.
2. Start the server.
3. Run the requests from top to bottom. They are in order: subjects, students, assessments, scores, then results.
   The collection already has the teacher login set, and the "error" folder shows what happens when things go wrong.

## How averages are worked out

Each score is turned into a percentage first: `score / max_score * 100`.
This matters because a test might be out of 20 and an exam out of 60, so you can't just add the raw marks.

- **Subject average** = average of the student's percentages in that subject
- **Overall average** = average of the subject averages
- **Class average** = average of all students' percentages in one subject

Example: Aisha scored 18/20 (90%) and 48/60 (80%) in Maths, and 14/20 (70%) in English.
Maths average = 85%, English = 70%, overall = 77.5%.

---

## How authentication, validation and error responses protect student results

### 1. Authentication (who are you, and what are you allowed to do?)

Every endpoint except `/` asks for a username and password. If they are missing or wrong, the API returns
**401 Unauthorized** and doesn't show any data.

After logging in, the API checks the user's **role**:

- Only the **teacher** can add or change scores. If a student tries to send `POST /scores` or `PUT /scores/1`
  they get **403 Forbidden**. This protects **accuracy**, because a student can't change their own marks.
- A **student** can only open their own results. If `STU002` tries to open `/students/STU001/results`
  they get **403 "You can only view your own results"**. This protects **privacy**, because students can't see each other's scores.
- Passwords are never sent back in any response (adding a student returns only the ID and name).
- Passwords are compared with `secrets.compare_digest` so the check takes the same time whether the guess is close or not.

### 2. Validation (is the data correct before it is saved?)

The Pydantic models in `models.py` check every request before it reaches the code that saves it:

- A score can't be negative (`ge=0`).
- A score can't be higher than the assessment's max score. 25 out of 20 is rejected.
- Student IDs must look like `STU001`, so typos like `stu1` or `abc` are caught.
- Subject names and titles can't be empty or too long, and max scores must be between 1 and 100.
- The same student can't get two scores for the same assessment. The second attempt returns **409 Conflict**
  and tells you to use PUT to update instead. This stops duplicate marks from messing up averages.
- A score can only be added for a student, assessment and subject that actually exist (**404** otherwise).

Without these checks, one bad entry (like 200 instead of 20) would quietly ruin the student's average
and nobody would know where it came from.

### 3. Clear error responses (what went wrong and how to fix it?)

Each error uses the right status code and a message a person can actually read:

| Code | When it happens | Example message |
|---|---|---|
| 401 | Wrong or missing login | `Incorrect username or password` |
| 403 | Logged in but not allowed | `Only the teacher can do this` |
| 404 | Something doesn't exist | `Student STU009 not found` |
| 409 | Duplicate data | `STU001 already has a score for this assessment (score id 1). Use PUT to update it.` |
| 422 | Data failed validation | `Score 25.0 is higher than the max score (20.0) for this assessment` |

Clear errors protect accuracy because the teacher knows straight away that a score was **not** saved and why,
so they can fix it instead of thinking it went through. They also don't leak private data. For example, a 403
doesn't show any of the other student's scores. It just says no.

## Things I would add next

- Store data in a real database (SQLite or PostgreSQL)
- Hash passwords instead of keeping them as plain text
- Use tokens (JWT) instead of Basic Auth, and always run over HTTPS
- Allow more than one teacher

## Author

Mukhtar Umar. FIP Deliverable B4
