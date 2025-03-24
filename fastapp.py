from fastapi import FastAPI, Request, Response, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from dotenv import load_dotenv
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="ILOVEYOU")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Update the templates configuration to include the static files
templates.env.globals["url_for"] = app.url_path_for

# Database configuration
load_dotenv()

# Update the DB_CONFIG section
DB_CONFIG = {
    'host': os.getenv('MYSQLHOST', 'localhost'),
    'user': os.getenv('MYSQLUSER', 'root'),
    'password': os.getenv('MYSQLPASSWORD', ''),
    'database': os.getenv('MYSQLDATABASE', 'snulms'),
    'port': int(os.getenv('MYSQLPORT', 3306))
}

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Helper function to get current user from session
async def get_current_user(request: Request):
    session = request.session
    if not session.get('loggedin'):
        return None
    return {
        'id': session.get('id'),
        'username': session.get('username'),
        'role': session.get('role')
    }

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/home")
    return templates.TemplateResponse("login.html", {"request": request, "msg": ""})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db)
):
    db.execute('SELECT * FROM users WHERE UserName = %s', (username,))
    account = db.fetchone()
    
    if account and check_password_hash(account['PasswordHash'], password):
        request.session['loggedin'] = True
        request.session['id'] = account['ID']
        request.session['username'] = account['UserName']
        request.session['role'] = account['Role']
        return RedirectResponse(url="/home", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "msg": "Incorrect username/password!"
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db)
):
    db.execute('SELECT DepartmentID, DepartmentName FROM department')
    departments = db.fetchall()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "departments": departments
    })

@app.post("/register")
async def register(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db)
):
    form = await request.form()
    try:
        # Common user details
        ID = int(form['ID'])
        username = form['username']
        password = form['password']
        firstname = form['firstname']
        lastname = form['lastname']
        email = form['email']
        role = form['role']
        
        hashed_password = generate_password_hash(password)
        
        # Insert into users table
        db.execute(
            'INSERT INTO users (ID, UserName, FirstName, LastName, Role, Email, PasswordHash) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (ID, username, firstname, lastname, role, email, hashed_password)
        )
        
        # Handle role-specific information
        if role == 'student':
            db.execute(
                'INSERT INTO student (ID, RegistrationNo, PhoneNo, Class, DoB, Semester, DepartmentID) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (ID, form['registration_no'], form['phone'], form['class'],
                 form['dob'], form['semester'], form['department_id'])
            )
        elif role == 'faculty':
            db.execute(
                'INSERT INTO faculty (ID, FacultyID, PhoneNo, Qualification, Level, DepartmentID) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (ID, form['faculty_id'], form['phone'], form['qualification'],
                 form['level'], form['department_id'])
            )
        
        return RedirectResponse(url="/login", status_code=303)
    
    except Error as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Database error: {str(e)}"
        })

@app.get("/home", response_class=HTMLResponse)
async def home(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login")
    
    if current_user['role'] == 'admin':
        # Get admin dashboard data
        db.execute('SELECT DepartmentID, DepartmentName FROM department')
        departments = db.fetchall()
        
        db.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = db.fetchone()['total_users']
        
        db.execute('SELECT COUNT(*) as total_courses FROM courses')
        total_courses = db.fetchone()['total_courses']
        
        db.execute('SELECT COUNT(*) as total_students FROM users WHERE Role = "student"')
        total_students = db.fetchone()['total_students']
        
        db.execute('SELECT COUNT(*) as total_faculty FROM users WHERE Role = "faculty"')
        total_faculty = db.fetchone()['total_faculty']
        
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "username": current_user['username'],
            "departments": departments,
            "total_users": total_users,
            "total_courses": total_courses,
            "total_students": total_students,
            "total_faculty": total_faculty
        })
    
    elif current_user['role'] == 'faculty':
        # Get faculty details
        db.execute('''
            SELECT f.*, d.DepartmentName
            FROM faculty f
            INNER JOIN department d ON f.DepartmentID = d.DepartmentID
            WHERE f.ID = %s
        ''', (current_user['id'],))
        faculty = db.fetchone()
        
        # Get faculty courses
        db.execute('''
            SELECT c.CourseID, c.CourseName, c.CourseCredit, c.Category, c.SemesterNo,
                   d.DepartmentName
            FROM courses c
            INNER JOIN department d ON c.DepartmentID = d.DepartmentID
            WHERE c.FacultyID = %s
        ''', (current_user['id'],))
        courses = db.fetchall()
        
        # Get recent assignments
        db.execute('''
            SELECT cc.CCName, cc.Description, cc.UploadDate, c.CourseName, c.CourseID
            FROM coursecontent cc
            INNER JOIN courses c ON cc.CourseID = c.CourseID
            WHERE cc.UploadedBy = %s AND cc.IsAssignment = 1
            ORDER BY cc.UploadDate DESC LIMIT 5
        ''', (current_user['id'],))
        assignments = db.fetchall()
        
        return templates.TemplateResponse("faculty_dashboard.html", {
            "request": request,
            "username": current_user['username'],
            "faculty": faculty,
            "courses": courses,
            "assignments": assignments
        })
    
    else:
        # Get student dashboard data
        db.execute('''
            SELECT c.CourseID, c.CourseName, c.CourseCredit,
                   f.FirstName as FacultyFirstName, f.LastName as FacultyLastName
            FROM courses c
            INNER JOIN faculty fac ON c.FacultyID = fac.ID
            INNER JOIN users f ON fac.ID = f.ID
            WHERE c.DepartmentID = (
                SELECT DepartmentID FROM student WHERE ID = %s
            )
        ''', (current_user['id'],))
        courses = db.fetchall()
        
        db.execute('''
            SELECT cc.CCName, cc.Description, cc.UploadDate
            FROM coursecontent cc
            INNER JOIN courses c ON cc.CourseID = c.CourseID
            WHERE cc.IsAssignment = 1 AND c.DepartmentID = (
                SELECT DepartmentID FROM student WHERE ID = %s
            )
            ORDER BY cc.UploadDate DESC LIMIT 5
        ''', (current_user['id'],))
        assignments = db.fetchall()
        
        return templates.TemplateResponse("student_dashboard.html", {
            "request": request,
            "username": current_user['username'],
            "courses": courses,
            "assignments": assignments
        })

@app.get("/course/{course_id}", response_class=HTMLResponse)
@app.post("/course/{course_id}", response_class=HTMLResponse)
async def course(
    course_id: str,
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Get course details
    db.execute('''
        SELECT c.*, d.DepartmentName,
               f.FirstName as FacultyFirstName, f.LastName as FacultyLastName
        FROM courses c
        INNER JOIN department d ON c.DepartmentID = d.DepartmentID
        INNER JOIN faculty fac ON c.FacultyID = fac.ID
        INNER JOIN users f ON fac.ID = f.ID
        WHERE c.CourseID = %s
    ''', (course_id,))
    course = db.fetchone()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get course content
    db.execute('''
        SELECT * FROM coursecontent 
        WHERE CourseID = %s 
        ORDER BY UploadDate DESC
    ''', (course_id,))
    contents = db.fetchall()
    
    is_faculty = (current_user['role'] == 'faculty' and 
                 current_user['id'] == course['FacultyID'])
    
    if request.method == "POST" and is_faculty:
        form = await request.form()
        if 'add_content' in form:
            db.execute('''
                INSERT INTO coursecontent 
                (CCName, Description, FileUrl, UploadDate, IsAssignment, CourseID, UploadedBy)
                VALUES (%s, %s, %s, CURDATE(), %s, %s, %s)
            ''', (
                form['content_name'],
                form['description'],
                form['file_url'],
                'is_assignment' in form,
                course_id,
                current_user['id']
            ))
            return RedirectResponse(url=f"/course/{course_id}", status_code=303)
    
    return templates.TemplateResponse("course.html", {
        "request": request,
        "course": course,
        "contents": contents,
        "is_faculty": is_faculty
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT u.*, 
               COALESCE(s.RegistrationNo, f.FacultyID) as identifier,
               d.DepartmentName
        FROM users u
        LEFT JOIN student s ON u.ID = s.ID
        LEFT JOIN faculty f ON u.ID = f.ID
        LEFT JOIN department d ON s.DepartmentID = d.DepartmentID 
            OR f.DepartmentID = d.DepartmentID
        ORDER BY u.Role, u.ID
    ''')
    users = db.fetchall()
    
    return templates.TemplateResponse("admin/manage_users.html", {
        "request": request,
        "users": users,
        "current_user": current_user,
        "active_page": "manage_users"
    })

@app.delete("/admin/users/delete/{user_id}")
async def delete_user(
    user_id: int,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Delete from specific role table first
        db.execute("SELECT Role FROM users WHERE ID = %s", (user_id,))
        user_role = db.fetchone()
        
        if user_role['Role'].lower() == 'student':
            db.execute("DELETE FROM student WHERE ID = %s", (user_id,))
        elif user_role['Role'].lower() == 'faculty':
            db.execute("DELETE FROM faculty WHERE ID = %s", (user_id,))
            
        # Then delete from users table
        db.execute("DELETE FROM users WHERE ID = %s", (user_id,))
        
        return {"success": True}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/courses", response_class=HTMLResponse)
async def admin_courses(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT c.*, d.DepartmentName,
               CONCAT(u.FirstName, ' ', u.LastName) as FacultyName
        FROM courses c
        INNER JOIN department d ON c.DepartmentID = d.DepartmentID
        INNER JOIN faculty f ON c.FacultyID = f.ID
        INNER JOIN users u ON f.ID = u.ID
        ORDER BY c.CourseID
    ''')
    courses = db.fetchall()
    
    db.execute('SELECT * FROM department')
    departments = db.fetchall()
    
    db.execute('''
        SELECT f.ID, CONCAT(u.FirstName, ' ', u.LastName) as Name
        FROM faculty f
        INNER JOIN users u ON f.ID = u.ID
    ''')
    faculty = db.fetchall()
    
    return templates.TemplateResponse("admin/manage_courses.html", {
        "request": request,
        "courses": courses,
        "departments": departments,
        "faculty": faculty,
        "current_user": current_user
    })

@app.post("/admin/courses/add")
async def add_course(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    form = await request.form()
    try:
        db.execute('''
            INSERT INTO courses (CourseID, CourseName, CourseCredit, Category, 
                               SemesterNo, DepartmentID, FacultyID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            form['course_id'], form['course_name'], form['credits'],
            form['category'], form['semester'], form['department_id'],
            form['faculty_id']
        ))
        return RedirectResponse(url="/admin/courses", status_code=303)
    except Error as e:
        return {"error": str(e)}

@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    # Get department-wise statistics
    db.execute('''
        SELECT d.DepartmentName,
               COUNT(DISTINCT s.ID) as student_count,
               COUNT(DISTINCT f.ID) as faculty_count,
               COUNT(DISTINCT c.CourseID) as course_count
        FROM department d
        LEFT JOIN student s ON d.DepartmentID = s.DepartmentID
        LEFT JOIN faculty f ON d.DepartmentID = f.DepartmentID
        LEFT JOIN courses c ON d.DepartmentID = c.DepartmentID
        GROUP BY d.DepartmentID
    ''')
    dept_stats = db.fetchall()

    db.execute('''
        SELECT 
            (SELECT COUNT(*) FROM student) as total_students,
            (SELECT COUNT(*) FROM faculty) as total_faculty,
            (SELECT COUNT(*) FROM courses) as total_courses,
            (SELECT COUNT(*) FROM department) as total_departments
    ''')
    summary_stats = db.fetchone()
    
    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "dept_stats": dept_stats,
        "current_user": current_user,
        **summary_stats
    })

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    db.execute('SELECT * FROM department')
    departments = db.fetchall()
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "departments": departments,
        "current_user": current_user
    })

@app.post("/admin/department/add")
async def add_department(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'admin':
        return RedirectResponse(url="/login")
    
    form = await request.form()
    try:
        db.execute('''
            INSERT INTO department (DepartmentID, DepartmentName)
            VALUES (%s, %s)
        ''', (form['dept_id'], form['dept_name']))
        return RedirectResponse(url="/admin/settings", status_code=303)
    except Error as e:
        return {"error": str(e)}

@app.get("/student/courses", response_class=HTMLResponse)
async def student_courses(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'student':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT c.*, f.FirstName as FacultyFirstName, f.LastName as FacultyLastName,
               (SELECT COUNT(*) FROM coursecontent WHERE CourseID = c.CourseID AND IsAssignment = 1) as assignments_count,
               (SELECT COALESCE(AVG(Attendance), 0) FROM attendance WHERE StudentID = %s AND CourseID = c.CourseID) as attendance_percentage
        FROM courses c
        INNER JOIN faculty fac ON c.FacultyID = fac.ID
        INNER JOIN users f ON fac.ID = f.ID
        WHERE c.DepartmentID = (SELECT DepartmentID FROM student WHERE ID = %s)
    ''', (current_user['id'], current_user['id']))
    courses = db.fetchall()
    
    return templates.TemplateResponse("student/courses.html", {
        "request": request,
        "courses": courses,
        "username": current_user['username']
    })

@app.get("/student/assignments", response_class=HTMLResponse)
async def student_assignments(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'student':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT cc.*, c.CourseName, c.CourseID,
               COALESCE(s.SubmissionDate, NULL) as submitted_date,
               COALESCE(s.Grade, NULL) as grade
        FROM coursecontent cc
        INNER JOIN courses c ON cc.CourseID = c.CourseID
        LEFT JOIN submissions s ON cc.CCID = s.CCID AND s.StudentID = %s
        WHERE cc.IsAssignment = 1 AND c.DepartmentID = (
            SELECT DepartmentID FROM student WHERE ID = %s
        )
        ORDER BY cc.UploadDate DESC
    ''', (current_user['id'], current_user['id']))
    assignments = db.fetchall()
    
    return templates.TemplateResponse("student/assignments.html", {
        "request": request,
        "assignments": assignments,
        "username": current_user['username']
    })

@app.get("/student/attendance", response_class=HTMLResponse)
async def student_attendance(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'student':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT c.CourseID, c.CourseName,
               COUNT(*) as total_classes,
               SUM(CASE WHEN a.Attendance = 1 THEN 1 ELSE 0 END) as attended_classes,
               (SUM(CASE WHEN a.Attendance = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as attendance_percentage
        FROM courses c
        LEFT JOIN attendance a ON c.CourseID = a.CourseID AND a.StudentID = %s
        WHERE c.DepartmentID = (SELECT DepartmentID FROM student WHERE ID = %s)
        GROUP BY c.CourseID
    ''', (current_user['id'], current_user['id']))
    attendance = db.fetchall()
    
    return templates.TemplateResponse("student/attendance.html", {
        "request": request,
        "attendance": attendance,
        "username": current_user['username']
    })

@app.get("/student/grades", response_class=HTMLResponse)
async def student_grades(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'student':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT c.CourseID, c.CourseName,
               AVG(s.Grade) as average_grade,
               COUNT(DISTINCT cc.CCID) as total_assignments,
               COUNT(s.SubmissionID) as submitted_assignments
        FROM courses c
        LEFT JOIN coursecontent cc ON c.CourseID = cc.CourseID AND cc.IsAssignment = 1
        LEFT JOIN submissions s ON cc.CCID = s.CCID AND s.StudentID = %s
        WHERE c.DepartmentID = (SELECT DepartmentID FROM student WHERE ID = %s)
        GROUP BY c.CourseID
    ''', (current_user['id'], current_user['id']))
    grades = db.fetchall()
    
    return templates.TemplateResponse("student/grades.html", {
        "request": request,
        "grades": grades,
        "username": current_user['username']
    })

@app.get("/student/profile", response_class=HTMLResponse)
async def student_profile(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'student':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT s.*, u.*, d.DepartmentName
        FROM student s
        INNER JOIN users u ON s.ID = u.ID
        INNER JOIN department d ON s.DepartmentID = d.DepartmentID
        WHERE s.ID = %s
    ''', (current_user['id'],))
    profile = db.fetchone()
    
    return templates.TemplateResponse("student/profile.html", {
        "request": request,
        "profile": profile,
        "username": current_user['username']
    })

@app.post("/faculty/assignment/add")
async def add_assignment(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    form = await request.form()
    course_id = form['course_id']
    name = form['name']
    description = form['description']
    due_date = form['due_date']
    total_marks = form['total_marks']
    
    db.execute('''
        INSERT INTO CourseContent 
        (CourseID, CCName, Description, UploadDate, DueDate, TotalMarks) 
        VALUES (%s, %s, %s, NOW(), %s, %s)
    ''', (course_id, name, description, due_date, total_marks))
    return RedirectResponse(url=f"/faculty/course/{course_id}", status_code=303)

@app.get("/faculty/courses")
async def faculty_courses(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT c.*, d.DepartmentName,
               (SELECT COUNT(*) FROM Enrollment WHERE CourseID = c.CourseID) as student_count,
               (SELECT COUNT(*) FROM CourseContent WHERE CourseID = c.CourseID AND IsAssignment = 1) as assignment_count
        FROM courses c
        JOIN department d ON c.DepartmentID = d.DepartmentID
        WHERE c.FacultyID = %s
    ''', (current_user['id'],))
    courses = db.fetchall()
    
    return templates.TemplateResponse("/faculty/faculty_courses.html", {
        "request": request,
        "courses": courses,
        "username": current_user['username']
    })

@app.get("/faculty/assignments")
async def faculty_assignments(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT cc.*, c.CourseName,
               (SELECT COUNT(*) FROM Submissions WHERE CCID = cc.CCID) as submission_count,
               (SELECT COUNT(*) FROM Enrollment WHERE CourseID = c.CourseID) as total_students
        FROM CourseContent cc
        JOIN courses c ON cc.CourseID = c.CourseID
        WHERE c.FacultyID = %s AND cc.IsAssignment = 1
        ORDER BY cc.UploadDate DESC
    ''', (current_user['id'],))
    assignments = db.fetchall()
    
    return templates.TemplateResponse("/faculty/faculty_assignments.html", {
        "request": request,
        "assignments": assignments,
        "username": current_user['username']
    })

@app.get("/faculty/reports")
async def faculty_reports(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    # Get course statistics
    db.execute('''
        SELECT c.CourseID, c.CourseName,
               COUNT(DISTINCT e.StudentID) as enrolled_students,
               COUNT(DISTINCT cc.CCID) as total_assignments,
               AVG(s.Grade) as average_grade,
               (SELECT AVG(Attendance) * 100 
                FROM attendance 
                WHERE CourseID = c.CourseID) as average_attendance
        FROM courses c
        LEFT JOIN enrollment e ON c.CourseID = e.CourseID
        LEFT JOIN coursecontent cc ON c.CourseID = cc.CourseID AND cc.IsAssignment = 1
        LEFT JOIN submissions s ON cc.CCID = s.CCID
        WHERE c.FacultyID = %s
        GROUP BY c.CourseID
    ''', (current_user['id'],))
    course_stats = db.fetchall()
    
    # Get assignment completion statistics
    db.execute('''
        SELECT cc.CCID, cc.CCName, c.CourseName,
               COUNT(DISTINCT s.StudentID) as submissions,
               (SELECT COUNT(*) FROM enrollment WHERE CourseID = c.CourseID) as total_students,
               AVG(s.Grade) as average_grade
        FROM coursecontent cc
        JOIN courses c ON cc.CourseID = c.CourseID
        LEFT JOIN submissions s ON cc.CCID = s.CCID
        WHERE c.FacultyID = %s AND cc.IsAssignment = 1
        GROUP BY cc.CCID
        ORDER BY cc.UploadDate DESC
    ''', (current_user['id'],))
    assignment_stats = db.fetchall()
    
    return templates.TemplateResponse("faculty/reports.html", {
        "request": request,
        "course_stats": course_stats,
        "assignment_stats": assignment_stats,
        "username": current_user['username']
    })

@app.get("/faculty/students")
async def faculty_students(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    # Get all students enrolled in faculty's courses
    db.execute('''
        SELECT DISTINCT 
            s.ID, s.RegistrationNo, u.FirstName, u.LastName,
            s.Semester, s.Class,
            d.DepartmentName,
            c.CourseID, c.CourseName,
            AVG(sub.Grade) as average_grade,
            (SELECT AVG(Attendance) * 100 
             FROM attendance 
             WHERE StudentID = s.ID AND CourseID = c.CourseID) as attendance_percentage
        FROM student s
        JOIN users u ON s.ID = u.ID
        JOIN department d ON s.DepartmentID = d.DepartmentID
        JOIN enrollment e ON s.ID = e.StudentID
        JOIN courses c ON e.CourseID = c.CourseID
        LEFT JOIN coursecontent cc ON c.CourseID = cc.CourseID AND cc.IsAssignment = 1
        LEFT JOIN submissions sub ON cc.CCID = sub.CCID AND sub.StudentID = s.ID
        WHERE c.FacultyID = %s
        GROUP BY s.ID, c.CourseID
        ORDER BY s.Semester, s.Class, u.FirstName
    ''', (current_user['id'],))
    students = db.fetchall()
    
    # Get course list for filtering
    db.execute('''
        SELECT CourseID, CourseName
        FROM courses
        WHERE FacultyID = %s
    ''', (current_user['id'],))
    courses = db.fetchall()
    
    return templates.TemplateResponse("faculty/students.html", {
        "request": request,
        "students": students,
        "courses": courses,
        "username": current_user['username']
    })

@app.get("/faculty/profile", response_class=HTMLResponse)
async def faculty_profile(
    request: Request,
    db: mysql.connector.cursor.MySQLCursor = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    # Get faculty profile with department and user details
    if not current_user or current_user['role'] != 'faculty':
        return RedirectResponse(url="/login")
    
    db.execute('''
        SELECT s.*, u.*, d.DepartmentName
        FROM faculty s
        INNER JOIN users u ON s.ID = u.ID
        INNER JOIN department d ON s.DepartmentID = d.DepartmentID
        WHERE s.ID = %s
    ''', (current_user['id'],))
    profile = db.fetchone()
    print(profile)
    
    return templates.TemplateResponse("faculty/profile.html", {
        "request": request,
        "profile": profile,
        "username": current_user['username']
    })

if __name__ == "__main__":
    uvicorn.run("fastapp:app", host="127.0.0.1", port=8000, reload=True)