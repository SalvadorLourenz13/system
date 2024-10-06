from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask_user'

mysql = MySQL(app)

# Generate a random join link
def generate_join_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@app.route('/')
def home():
    if 'username' in session and 'role' in session:
        return render_template('home.html', username=session['username'], role=session['role'])
    else:
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT username, email, password, role, is_approved FROM tbl_user WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user:
            if not user[4]:  # If user is not approved
                return render_template('login.html', error='Your account has not been approved yet. Please wait for admin approval.')
            if pwd == user[3]:  # Check if the password matches
                session['username'] = user[1]  # Store username
                session['email'] = user[2]     # Store email
                session['role'] = user[4]      # Store role

                # Role-based redirect
                if user[4] == 'teacher':
                    return redirect(url_for('teacher'))
                elif user[4] == 'student':
                    return redirect(url_for('student'))
                else:
                    return render_template('login.html', error='Invalid Role')
            else:
                return render_template('login.html', error='Invalid Username or Password')
        else:
            return render_template('login.html', error='Invalid Username or Password')
    return render_template('login.html')



# Signup route - students and teachers are not auto-approved
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        pwd = request.form['password']
        role = request.form['role']

        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM tbl_user WHERE email = %s", [email])
        existing_email = cur.fetchone()

        if existing_email:
            return render_template('signup.html', error='Email is already registered. Please use another email.')

        # Insert new user, default approval to False
        cur.execute("INSERT INTO tbl_user (username, email, password, role, is_approved) VALUES (%s, %s, %s, %s, %s)", 
                    (username, email, pwd, role, False))
        mysql.connection.commit()
        cur.close()

        flash('Signup successful. Please wait for admin approval.')
        return redirect(url_for('login'))
    return render_template('signup.html')

# Admin dashboard - approve/reject users
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'role' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT username, email, role, is_approved FROM tbl_user WHERE is_approved = FALSE")
        users = cur.fetchall()  # Fetch the list of unapproved users
        cur.close()
        return render_template('admin.html', users=users)  # Pass the list to the template
    else:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))

# Teacher section - send a join link to students
@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if 'role' in session and session['role'] == 'teacher':
        join_link = generate_join_link()
        flash(f'Send this join link to students: {join_link}')
        return render_template('teacher.html', join_link=join_link)
    else:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))

# Student section - join using a link provided by the teacher
@app.route('/student', methods=['GET', 'POST'])
def student():
    if 'role' in session and session['role'] == 'student':
        if request.method == 'POST':
            entered_link = request.form['join_link']
            if entered_link:
                flash(f'You successfully joined with link: {entered_link}')
                return render_template('student.html')
            else:
                flash('Invalid or missing join link.')
                return render_template('student.html')
        return render_template('student.html')
    else:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)