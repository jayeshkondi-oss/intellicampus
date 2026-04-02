"""Teacher blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from db import get_db
from utils.helpers import save_file
import datetime

teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'teacher':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_teacher_id():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id FROM teachers WHERE user_id=%s", (current_user.id,))
    row = cur.fetchone(); cur.close()
    return row['id'] if row else None

def get_teacher_subjects(cur, tid):
    """Get subjects assigned to teacher. Falls back to dept subjects if none assigned."""
    cur.execute("""SELECT DISTINCT s.id,s.name,s.code,s.semester,s.year,s.department_id
                   FROM subjects s
                   JOIN teacher_subjects ts ON ts.subject_id=s.id
                   WHERE ts.teacher_id=%s ORDER BY s.semester,s.name""", (tid,))
    subjects = cur.fetchall()
    if not subjects:
        # Fallback: show all subjects in teacher's department
        cur.execute("""SELECT DISTINCT s.id,s.name,s.code,s.semester,s.year,s.department_id
                       FROM subjects s
                       JOIN teachers t ON t.department_id=s.department_id
                       WHERE t.id=%s ORDER BY s.semester,s.name""", (tid,))
        subjects = cur.fetchall()
    return subjects


# ── Dashboard ─────────────────────────────────────────────────
@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    today = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][datetime.datetime.today().weekday()]
    cur.execute("""SELECT tt.*,s.name AS sub_name,s.code,c.name AS room
                   FROM timetable tt JOIN subjects s ON s.id=tt.subject_id
                   LEFT JOIN classrooms c ON c.id=tt.classroom_id
                   WHERE tt.teacher_id=%s AND tt.day_of_week=%s ORDER BY tt.start_time""", (tid,today))
    today_classes = cur.fetchall()
    cur.execute("""SELECT a.*,s.name AS sub_name FROM assignments a
                   JOIN subjects s ON s.id=a.subject_id
                   WHERE a.teacher_id=%s AND a.due_date>NOW() ORDER BY a.due_date LIMIT 5""", (tid,))
    upcoming_assignments = cur.fetchall()
    cur.execute("""SELECT COUNT(*) AS cnt FROM submissions sub
                   JOIN assignments a ON a.id=sub.assignment_id
                   WHERE a.teacher_id=%s AND sub.status='Submitted'""", (tid,))
    pending_reviews = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(DISTINCT student_id) AS cnt FROM attendance WHERE teacher_id=%s", (tid,))
    total_students = cur.fetchone()['cnt']
    
    # Subject-wise attendance for charts
    cur.execute("""SELECT s.name AS sub_name,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS att_pct
                   FROM attendance a JOIN subjects s ON s.id=a.subject_id
                   WHERE a.teacher_id=%s GROUP BY a.subject_id,s.name ORDER BY s.name""", (tid,))
    subject_att_data = cur.fetchall()
    
    cur.close()
    return render_template('teacher/dashboard.html', today_classes=today_classes,
        upcoming_assignments=upcoming_assignments, pending_reviews=pending_reviews,
        total_students=total_students, today=today, subject_att_data=subject_att_data)

# ── Attendance ────────────────────────────────────────────────
@teacher_bp.route('/attendance')
@teacher_required
def attendance():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    subjects = get_teacher_subjects(cur, tid)
    cur.close()
    return render_template('teacher/attendance.html', subjects=subjects)

@teacher_bp.route('/attendance/mark', methods=['GET','POST'])
@teacher_required
def mark_attendance():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    subjects = get_teacher_subjects(cur, tid)
    students=[]; selected_sub=None; selected_date=None; selected_subject=None

    if request.method=='GET' and request.args.get('subject_id'):
        selected_sub  = request.args.get('subject_id')
        selected_date = request.args.get('date', datetime.date.today().isoformat())
        cur.execute("""SELECT s.id,s.name,s.code,s.semester,d.name AS dept_name
                       FROM subjects s JOIN departments d ON d.id=s.department_id
                       WHERE s.id=%s""", (selected_sub,))
        selected_subject = cur.fetchone()
        cur.execute("""SELECT s.id,u.full_name,s.roll_number,
                              COALESCE((SELECT status FROM attendance
                               WHERE student_id=s.id AND subject_id=%s AND date=%s),'') AS existing_status
                       FROM students s JOIN users u ON u.id=s.user_id
                       WHERE s.department_id=(SELECT department_id FROM subjects WHERE id=%s)
                         AND s.semester=(SELECT semester FROM subjects WHERE id=%s)
                       ORDER BY s.roll_number""",
                    (selected_sub,selected_date,selected_sub,selected_sub))
        students = cur.fetchall()

    if request.method=='POST':
        sub_id=request.form.get('subject_id'); date=request.form.get('date')
        for key,val in request.form.items():
            if key.startswith('status_'):
                stu_id=key.split('_')[1]
                cur.execute("""INSERT INTO attendance (student_id,subject_id,teacher_id,date,status)
                               VALUES(%s,%s,%s,%s,%s)
                               ON DUPLICATE KEY UPDATE status=%s,teacher_id=%s""",
                            (stu_id,sub_id,tid,date,val,val,tid))
        db.commit()
        flash('Attendance saved!', 'success')
        return redirect(url_for('teacher.attendance'))
    cur.close()
    return render_template('teacher/mark_attendance.html', subjects=subjects,
        students=students, selected_sub=selected_sub, selected_date=selected_date,
        selected_subject=selected_subject)

@teacher_bp.route('/attendance/report')
@teacher_required
def attendance_report():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.full_name,st.roll_number,sub.name AS sub_name,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          COUNT(*) AS total,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS pct
                   FROM attendance a JOIN students st ON st.id=a.student_id
                   JOIN users u ON u.id=st.user_id JOIN subjects sub ON sub.id=a.subject_id
                   WHERE a.teacher_id=%s GROUP BY a.student_id,a.subject_id,u.full_name,st.roll_number,sub.name
                   ORDER BY sub.name,st.roll_number""", (tid,))
    report = cur.fetchall()
    
    # Calculate chart data
    good_students = sum(1 for r in report if (r['pct'] or 0) >= 75)
    warning_students = sum(1 for r in report if 60 <= (r['pct'] or 0) < 75)
    danger_students = sum(1 for r in report if (r['pct'] or 0) < 60)
    
    cur.close()
    return render_template('teacher/attendance_report.html', report=report,
        good_students=good_students, warning_students=warning_students, danger_students=danger_students)

@teacher_bp.route('/attendance/report/export')
@teacher_required
def export_attendance_report():
    import csv, io
    from flask import Response
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.full_name,st.roll_number,sub.name AS sub_name,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          COUNT(*) AS total,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS pct
                   FROM attendance a JOIN students st ON st.id=a.student_id
                   JOIN users u ON u.id=st.user_id JOIN subjects sub ON sub.id=a.subject_id
                   WHERE a.teacher_id=%s GROUP BY a.student_id,a.subject_id,u.full_name,st.roll_number,sub.name
                   ORDER BY sub.name,st.roll_number""", (tid,))
    report = cur.fetchall(); cur.close()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Student Name', 'Roll Number', 'Subject', 'Present', 'Absent', 'Total Classes', 'Attendance %'])
    
    for row in report:
        writer.writerow([
            row['full_name'], 
            row['roll_number'], 
            row['sub_name'], 
            row['present'], 
            row['absent'], 
            row['total'], 
            f"{row['pct']}%"
        ])
    
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=attendance_report.csv"})

# ── Assignments ───────────────────────────────────────────────
@teacher_bp.route('/assignments')
@teacher_required
def assignments():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT a.*,s.name AS sub_name,d.name AS dept,COUNT(sub.id) AS submission_count
                   FROM assignments a JOIN subjects s ON s.id=a.subject_id
                   JOIN departments d ON d.id=a.department_id
                   LEFT JOIN submissions sub ON sub.assignment_id=a.id
                   WHERE a.teacher_id=%s GROUP BY a.id ORDER BY a.created_at DESC""", (tid,))
    assignments = cur.fetchall(); cur.close()
    return render_template('teacher/assignments.html', assignments=assignments)

@teacher_bp.route('/assignments/create', methods=['GET','POST'])
@teacher_required
def create_assignment():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    subjects = get_teacher_subjects(cur, tid)
    cur.execute("SELECT * FROM departments"); depts = cur.fetchall()
    error = None
    if request.method=='POST':
        f=request.form
        try:
            cur.execute("""INSERT INTO assignments
                (title,description,subject_id,teacher_id,semester,department_id,due_date,max_marks)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
                (f['title'],f.get('description'),f['subject_id'],tid,
                 f['semester'],f['department_id'],f['due_date'],f.get('max_marks',10)))
            db.commit()
            flash('Assignment created!', 'success')
            return redirect(url_for('teacher.assignments'))
        except Exception as e:
            db.rollback(); error=str(e)
        finally:
            cur.close()
    return render_template('teacher/create_assignment.html', subjects=subjects, depts=depts, error=error)

@teacher_bp.route('/assignments/<int:aid>/submissions')
@teacher_required
def view_submissions(aid):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM assignments WHERE id=%s", (aid,)); assignment=cur.fetchone()
    cur.execute("""SELECT sub.*,u.full_name,st.roll_number
                   FROM submissions sub JOIN students st ON st.id=sub.student_id
                   JOIN users u ON u.id=st.user_id
                   WHERE sub.assignment_id=%s ORDER BY sub.submitted_at""", (aid,))
    submissions=cur.fetchall(); cur.close()
    return render_template('teacher/submissions.html', assignment=assignment, submissions=submissions)

@teacher_bp.route('/submissions/<int:sub_id>/grade', methods=['POST'])
@teacher_required
def grade_submission(sub_id):
    marks=request.form.get('marks'); feedback=request.form.get('feedback')
    aid=request.form.get('assignment_id')
    db=get_db(); cur=db.cursor()
    cur.execute("UPDATE submissions SET marks_obtained=%s,feedback=%s,status='Graded' WHERE id=%s",
                (marks,feedback,sub_id))
    db.commit(); cur.close()
    flash('Graded!', 'success')
    return redirect(url_for('teacher.view_submissions', aid=aid))

# ── Exams & Marks ─────────────────────────────────────────────
@teacher_bp.route('/exams')
@teacher_required
def exams():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT s.id,s.name,s.code,s.semester,s.year,s.department_id
                   FROM subjects s
                   JOIN teacher_subjects ts ON ts.subject_id=s.id
                   WHERE ts.teacher_id=%s
                   ORDER BY s.semester,s.name""", (tid,))
    subjects = cur.fetchall()
    cur.close()
    # Quick stats for dashboard
    sem_counts = {}
    for s in subjects:
        sem = s['semester']
        sem_counts[sem] = sem_counts.get(sem, 0) + 1
    total_subjects = len(subjects)
    semesters_covered = len(sem_counts)
    max_semester = max(sem_counts.keys()) if sem_counts else 0
    top_semester = max(sem_counts, key=sem_counts.get) if sem_counts else 0
    top_semester_count = sem_counts.get(top_semester, 0)
    max_sem_count = max(sem_counts.values()) if sem_counts else 0
    return render_template('teacher/exams.html',
        subjects=subjects,
        sem_counts=sem_counts,
        total_subjects=total_subjects,
        semesters_covered=semesters_covered,
        max_semester=max_semester,
        top_semester=top_semester,
        top_semester_count=top_semester_count,
        max_sem_count=max_sem_count)

@teacher_bp.route('/exams/subject/<int:subject_id>', methods=['GET','POST'])
@teacher_required
def enter_subject_marks(subject_id):
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT s.*,d.name AS dept_name
                   FROM subjects s
                   JOIN teacher_subjects ts ON ts.subject_id=s.id
                   JOIN departments d ON d.id=s.department_id
                   WHERE ts.teacher_id=%s AND s.id=%s""", (tid,subject_id))
    subject = cur.fetchone()
    if not subject:
        cur.close()
        flash('Subject not assigned to you.', 'danger')
        return redirect(url_for('teacher.exams'))

    def ensure_exam(name, default_max):
        cur.execute("SELECT * FROM exams WHERE subject_id=%s AND name=%s ORDER BY id DESC LIMIT 1",
                    (subject_id, name))
        exam = cur.fetchone()
        if not exam:
            cur.execute("""INSERT INTO exams
                           (name,subject_id,department_id,semester,exam_date,max_marks)
                           VALUES(%s,%s,%s,%s,%s,%s)""",
                        (name, subject_id, subject['department_id'], subject['semester'], None, default_max))
            db.commit()
            cur.execute("SELECT * FROM exams WHERE id=LAST_INSERT_ID()")
            exam = cur.fetchone()
        return exam

    internal_exam = ensure_exam('Internal', 30)
    external_exam = ensure_exam('External', 70)

    cur.execute("""SELECT st.id,u.full_name,st.roll_number,
                          COALESCE(mi.marks_obtained,'') AS internal_marks,
                          COALESCE(me.marks_obtained,'') AS external_marks
                   FROM students st JOIN users u ON u.id=st.user_id
                   LEFT JOIN marks mi ON mi.student_id=st.id AND mi.exam_id=%s
                   LEFT JOIN marks me ON me.student_id=st.id AND me.exam_id=%s
                   WHERE st.department_id=%s AND st.semester=%s
                   ORDER BY st.roll_number""",
                (internal_exam['id'], external_exam['id'], subject['department_id'], subject['semester']))
    students = cur.fetchall()

    if request.method=='POST':
        # Optional max marks update
        internal_max = request.form.get('internal_max', '').strip()
        external_max = request.form.get('external_max', '').strip()
        if internal_max:
            cur.execute("UPDATE exams SET max_marks=%s WHERE id=%s", (internal_max, internal_exam['id']))
            internal_exam['max_marks'] = internal_max
        if external_max:
            cur.execute("UPDATE exams SET max_marks=%s WHERE id=%s", (external_max, external_exam['id']))
            external_exam['max_marks'] = external_max

        def norm(v):
            v = (v or '').strip()
            return v if v != '' else None

        for st in students:
            iid = st['id']
            im = norm(request.form.get(f'internal_{iid}'))
            em = norm(request.form.get(f'external_{iid}'))
            cur.execute("""INSERT INTO marks (exam_id,student_id,marks_obtained,grade,entered_by)
                           VALUES(%s,%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE marks_obtained=%s,grade=%s,entered_by=%s""",
                        (internal_exam['id'], iid, im, None, tid, im, None, tid))
            cur.execute("""INSERT INTO marks (exam_id,student_id,marks_obtained,grade,entered_by)
                           VALUES(%s,%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE marks_obtained=%s,grade=%s,entered_by=%s""",
                        (external_exam['id'], iid, em, None, tid, em, None, tid))
        db.commit()
        flash('Marks saved!', 'success')
        return redirect(url_for('teacher.enter_subject_marks', subject_id=subject_id))
    cur.close()
    return render_template('teacher/enter_subject_marks.html',
        subject=subject, internal_exam=internal_exam, external_exam=external_exam,
        students=students)

# ── PYQ Upload ────────────────────────────────────────────────
@teacher_bp.route('/pyq/upload', methods=['GET','POST'])
@teacher_required
def upload_pyq():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT s.*, d.name AS dept
                   FROM subjects s
                   JOIN departments d ON d.id=s.department_id
                   ORDER BY d.name, s.semester, s.name""")
    subjects = cur.fetchall()
    cur.execute("SELECT id, name FROM departments ORDER BY name")
    departments = cur.fetchall()
    error = None
    if request.method=='POST':
        f=request.form
        fname = save_file(request.files.get('pyq_file'), prefix='pyq')
        if fname:
            cur.execute("""INSERT INTO pyq_papers
                (subject_id,department_id,semester,exam_year,exam_type,file_path,uploaded_by)
                VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (f['subject_id'],f['department_id'],f['semester'],
                 f['exam_year'],f.get('exam_type'),fname,current_user.id))
            db.commit()
            flash('PYQ uploaded!', 'success')
            return redirect(url_for('teacher.upload_pyq'))
        else:
            error='Invalid file type. Allowed: pdf, doc, docx, png, jpg.'
    cur.close()
    return render_template('teacher/upload_pyq.html',
                           subjects=subjects,
                           departments=departments,
                           error=error)

# ── Profile & Leave ───────────────────────────────────────────
@teacher_bp.route('/profile')
@teacher_required
def profile():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.*,t.*,d.name AS dept_name FROM users u
                   JOIN teachers t ON t.user_id=u.id JOIN departments d ON d.id=t.department_id
                   WHERE u.id=%s""", (current_user.id,))
    profile=cur.fetchone(); cur.close()
    return render_template('teacher/profile.html', profile=profile)

@teacher_bp.route('/leave', methods=['GET','POST'])
@teacher_required
def apply_leave():
    tid = get_teacher_id()
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM leave_applications WHERE teacher_id=%s ORDER BY applied_at DESC",(tid,))
    leaves=cur.fetchall()
    if request.method=='POST':
        f=request.form
        cur.execute("INSERT INTO leave_applications (teacher_id,from_date,to_date,reason) VALUES(%s,%s,%s,%s)",
                    (tid,f['from_date'],f['to_date'],f['reason']))
        db.commit()
        flash('Leave application submitted!', 'success')
        return redirect(url_for('teacher.apply_leave'))
    cur.close()
    return render_template('teacher/leave.html', leaves=leaves)
