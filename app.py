from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DB_FILE = 'students.db'

# Profile icons for different genders
PROFILE_ICONS = {
    'Male': [f"https://github.com/UXHERI/students-app/blob/main/profile_icons/Male/{i}.png?raw=true" for i in range(1, 50)],
    'Female': [f"https://github.com/UXHERI/students-app/blob/main/profile_icons/Female/{i}.png?raw=true" for i in range(1, 31)]
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    roll_no TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    contact TEXT,
                    gender TEXT,
                    image TEXT
                )''')
    conn.commit()
    conn.close()

def get_random_profile(gender):
    """Get random profile image based on gender"""
    if gender in PROFILE_ICONS and PROFILE_ICONS[gender]:
        return random.choice(PROFILE_ICONS[gender])
    # Fallback default icon
    return "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"

@app.route('/')
def index():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM students ORDER BY name")
        students = c.fetchall()
        conn.close()
        return render_template('index.html', students=students)
    except Exception as e:
        flash(f"Error loading students: {str(e)}", "error")
        return render_template('index.html', students=[])

@app.route('/add', methods=['POST'])
def add_student():
    try:
        roll_no = request.form['roll_no'].strip()
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        contact = request.form['contact'].strip()
        gender = request.form['gender']

        # Basic validation
        if not all([roll_no, name, email, gender]):
            flash("Please fill all required fields", "error")
            return redirect('/')

        # Check if roll number already exists
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT roll_no FROM students WHERE roll_no = ?", (roll_no,))
        if c.fetchone():
            flash("Student with this Roll No already exists", "error")
            conn.close()
            return redirect('/')

        # Get random profile image based on gender
        image = get_random_profile(gender)

        c.execute("INSERT INTO students (roll_no, name, email, contact, gender, image) VALUES (?, ?, ?, ?, ?, ?)",
                  (roll_no, name, email, contact, gender, image))
        conn.commit()
        conn.close()
        
        flash("Student added successfully!", "success")
        return redirect('/')

    except Exception as e:
        flash(f"Error adding student: {str(e)}", "error")
        return redirect('/')

@app.route('/delete/<roll_no>', methods=['POST'])
def delete_student(roll_no):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
        conn.commit()
        conn.close()
        flash("Student deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting student: {str(e)}", "error")
    return redirect('/')

@app.route('/edit/<roll_no>', methods=['GET', 'POST'])
def edit_student(roll_no):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        if request.method == 'POST':
            name = request.form['name'].strip()
            email = request.form['email'].strip()
            contact = request.form['contact'].strip()
            gender = request.form['gender']

            c.execute("UPDATE students SET name=?, email=?, contact=?, gender=? WHERE roll_no=?",
                      (name, email, contact, gender, roll_no))
            conn.commit()
            conn.close()
            flash("Student updated successfully!", "success")
            return redirect('/')
        else:
            c.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
            student = c.fetchone()
            conn.close()
            
            if not student:
                flash("Student not found", "error")
                return redirect('/')
            
            return render_template('edit_student.html', student=student)
            
    except Exception as e:
        flash(f"Error updating student: {str(e)}", "error")
        return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)