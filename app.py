from flask import Flask, request, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__, static_url_path='', static_folder='static')


app.secret_key = "PASSWORDISIDK"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'snulms'

mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to home
    if 'loggedin' in session:
        return redirect(url_for('home'))
        
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE UserName = %s', [username])
        account = cursor.fetchone()
        
        if account and check_password_hash(account['PasswordHash'], password):
            session['loggedin'] = True
            session['id'] = account['ID']
            session['username'] = account['UserName']
            session['role'] = account['Role']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Common user details
        ID = int(request.form['ID'])
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        role = request.form['role']
        
        hashed_password = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        try:
            # Insert into users table
            cursor.execute('INSERT INTO users (ID, UserName, FirstName, LastName, Role, Email, PasswordHash) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                          (ID, username, firstname, lastname, role, email, hashed_password))
            
            # Handle role-specific information
            if role == 'student':
                reg_no = int(request.form['registration_no'])
                phone = int(request.form['phone'])
                student_class = request.form['class']
                dob = request.form['dob']
                semester = request.form['semester']
                department_id = int(request.form['department_id'])
                
                cursor.execute('INSERT INTO student (ID, RegistrationNo, PhoneNo, Class, DoB, Semester, DepartmentID) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                             (ID, reg_no, phone, student_class, dob, semester, department_id))
                
            elif role == 'faculty':
                faculty_id = int(request.form['faculty_id'])
                phone = int(request.form['phone'])
                qualification = request.form['qualification']
                level = request.form['level']
                department_id = int(request.form['department_id'])
                
                cursor.execute('INSERT INTO faculty (ID, FacultyID, PhoneNo, Qualification, Level, DepartmentID) VALUES (%s, %s, %s, %s, %s, %s)',
                             (ID, faculty_id, phone, qualification, level, department_id))
            
            mysql.connection.commit()
            return redirect(url_for('login'))
            
        except MySQLdb.Error as e:
            mysql.connection.rollback()
            return render_template('register.html', error=f"Database error: {str(e)}")
            
    # Get departments for the registration form
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT DepartmentID, DepartmentName FROM department')
    departments = cursor.fetchall()
    return render_template('register.html', departments=departments)

@app.route('/home')
def home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if session['role'] == 'admin':
        # Get departments for the form
        cursor.execute('SELECT DepartmentID, DepartmentName FROM department')
        departments = cursor.fetchall()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as total_courses FROM courses')
        total_courses = cursor.fetchone()['total_courses']
        
        cursor.execute('SELECT COUNT(*) as total_students FROM users WHERE Role = "student"')
        total_students = cursor.fetchone()['total_students']
        
        cursor.execute('SELECT COUNT(*) as total_faculty FROM users WHERE Role = "faculty"')
        total_faculty = cursor.fetchone()['total_faculty']
        
        return render_template('admin_dashboard.html', 
                             username=session['username'],
                             departments=departments,
                             total_users=total_users,
                             total_courses=total_courses,
                             total_students=total_students,
                             total_faculty=total_faculty)
    
    elif session['role'] == 'faculty':
        # Fetch courses taught by faculty
        cursor.execute('''
            SELECT c.CourseID, c.CourseName, c.CourseCredit, c.Category, c.SemesterNo,
                   d.DepartmentName
            FROM courses c
            INNER JOIN department d ON c.DepartmentID = d.DepartmentID
            WHERE c.FacultyID = %s
        ''', [session['id']])
        courses = cursor.fetchall()
        
        # Fetch assignments created by faculty
        cursor.execute('''
            SELECT cc.CCName, cc.Description, cc.UploadDate, c.CourseName
            FROM coursecontent cc
            INNER JOIN courses c ON cc.CourseID = c.CourseID
            WHERE cc.UploadedBy = %s AND cc.IsAssignment = 1
            ORDER BY cc.UploadDate DESC
            LIMIT 5
        ''', [session['id']])
        assignments = cursor.fetchall()
        
        # Get faculty details
        cursor.execute('''
            SELECT f.*, d.DepartmentName
            FROM faculty f
            INNER JOIN department d ON f.DepartmentID = d.DepartmentID
            WHERE f.ID = %s
        ''', [session['id']])
        faculty_details = cursor.fetchone()
        
        return render_template('faculty_dashboard.html',
                             username=session['username'],
                             courses=courses,
                             assignments=assignments,
                             faculty=faculty_details)
    
    else:
        # Fetch enrolled courses for student
        cursor.execute('''
            SELECT c.CourseID, c.CourseName, c.CourseCredit, 
                   f.FirstName as FacultyFirstName, f.LastName as FacultyLastName
            FROM courses c
            INNER JOIN faculty fac ON c.FacultyID = fac.ID
            INNER JOIN users f ON fac.ID = f.ID
            WHERE c.DepartmentID = (
                SELECT DepartmentID 
                FROM student 
                WHERE ID = %s
            )
        ''', [session['id']])
        courses = cursor.fetchall()
        
        # Fetch upcoming assignments
        cursor.execute('''
            SELECT cc.CCName, cc.Description, cc.UploadDate
            FROM coursecontent cc
            INNER JOIN courses c ON cc.CourseID = c.CourseID
            WHERE cc.IsAssignment = 1 AND c.DepartmentID = (
                SELECT DepartmentID 
                FROM student 
                WHERE ID = %s
            )
            ORDER BY cc.UploadDate DESC
            LIMIT 5
        ''', [session['id']])
        assignments = cursor.fetchall()
        
        return render_template('student_dashboard.html', 
                             username=session['username'],
                             courses=courses,
                             assignments=assignments)

@app.route('/course/<course_id>', methods=['GET', 'POST'])
def course(course_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get course details
    cursor.execute('''
        SELECT c.*, d.DepartmentName,
               f.FirstName as FacultyFirstName, f.LastName as FacultyLastName
        FROM courses c
        INNER JOIN department d ON c.DepartmentID = d.DepartmentID
        INNER JOIN faculty fac ON c.FacultyID = fac.ID
        INNER JOIN users f ON fac.ID = f.ID
        WHERE c.CourseID = %s
    ''', [course_id])
    course = cursor.fetchone()
    
    if not course:
        return "Course not found", 404
    
    # Get course content
    cursor.execute('''
        SELECT * FROM coursecontent 
        WHERE CourseID = %s 
        ORDER BY UploadDate DESC
    ''', [course_id])
    contents = cursor.fetchall()
    
    is_faculty = session['role'] == 'faculty' and session['id'] == course['FacultyID']
    
    if request.method == 'POST' and is_faculty:
        if 'add_content' in request.form:
            name = request.form['content_name']
            description = request.form['description']
            file_url = request.form['file_url']
            is_assignment = 'is_assignment' in request.form
            
            cursor.execute('''
                INSERT INTO coursecontent 
                (CCName, Description, FileUrl, UploadDate, IsAssignment, CourseID, UploadedBy)
                VALUES (%s, %s, %s, CURDATE(), %s, %s, %s)
            ''', (name, description, file_url, is_assignment, course_id, session['id']))
            mysql.connection.commit()
            return redirect(url_for('course', course_id=course_id))
    
    return render_template('course.html',
                         course=course,
                         contents=contents,
                         is_faculty=is_faculty)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)