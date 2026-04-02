"""Student blueprint — subjects come from teacher_subjects (what teachers are assigned)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from functools import wraps
from db import get_db
from utils.helpers import save_file
from utils.pyq_scraper import fetch_pyq_papers, get_source_url
import datetime

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        # Prevent redirect loops if a user lacks a student profile
        if not get_student():
            flash('Student profile not found. Please contact admin.', 'danger')
            logout_user()
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_student():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT s.*,d.name AS dept_name,d.code AS dept_code
                   FROM students s JOIN departments d ON d.id=s.department_id
                   WHERE s.user_id=%s""", (current_user.id,))
    row = cur.fetchone(); cur.close()
    return row

# ── Dashboard ─────────────────────────────────────────────────
@student_bp.route('/dashboard')
@student_required
def dashboard():
    stu = get_student()
    if not stu:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))
    db = get_db(); cur = db.cursor()
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    today = days[datetime.datetime.today().weekday()]
    cur.execute("""SELECT tt.*,s.name AS sub_name,s.code,u.full_name AS teacher,c.name AS room
                   FROM timetable tt JOIN subjects s ON s.id=tt.subject_id
                   JOIN teachers te ON te.id=tt.teacher_id JOIN users u ON u.id=te.user_id
                   LEFT JOIN classrooms c ON c.id=tt.classroom_id
                   WHERE tt.department_id=%s AND tt.semester=%s AND tt.day_of_week=%s
                   ORDER BY tt.start_time""", (stu['department_id'], stu['semester'], today))
    today_classes = cur.fetchall()
    cur.execute("SELECT ROUND(SUM(status='Present')/COUNT(*)*100,1) AS pct FROM attendance WHERE student_id=%s", (stu['id'],))
    att_row = cur.fetchone(); attendance_pct = att_row['pct'] if att_row['pct'] else 0
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM fees WHERE student_id=%s AND status='Pending'", (stu['id'],))
    pending_fee = cur.fetchone()['total']
    cur.execute("""SELECT a.*,s.name AS sub_name FROM assignments a JOIN subjects s ON s.id=a.subject_id
                   WHERE a.department_id=%s AND a.semester=%s AND a.due_date>NOW()
                     AND a.id NOT IN (SELECT assignment_id FROM submissions WHERE student_id=%s)
                   ORDER BY a.due_date LIMIT 5""", (stu['department_id'], stu['semester'], stu['id']))
    pending_assignments = cur.fetchall()
    
    # Total vs Completed Assignments for Gauge Chart
    cur.execute("SELECT COUNT(*) AS cnt FROM assignments WHERE department_id=%s AND semester=%s", (stu['department_id'], stu['semester']))
    total_assignments = cur.fetchone()['cnt'] or 0
    cur.execute("SELECT COUNT(DISTINCT assignment_id) AS cnt FROM submissions WHERE student_id=%s", (stu['id'],))
    completed_assignments = cur.fetchone()['cnt'] or 0
    
    # Subject-wise attendance for charts
    cur.execute("""SELECT s.name AS sub_name,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS att_pct
                   FROM attendance a JOIN subjects s ON s.id=a.subject_id
                   WHERE a.student_id=%s GROUP BY a.subject_id,s.name ORDER BY s.name""", (stu['id'],))
    subject_att_data = cur.fetchall()
    
    cur.close()
    return render_template('student/dashboard.html', stu=stu, today_classes=today_classes,
        attendance_pct=attendance_pct, pending_fee=pending_fee,
        pending_assignments=pending_assignments, today=today, subject_att_data=subject_att_data,
        total_assignments=total_assignments, completed_assignments=completed_assignments)

# ── Timetable ─────────────────────────────────────────────────
@student_bp.route('/timetable')
@student_required
def timetable():
    stu = get_student(); db = get_db(); cur = db.cursor()
    cur.execute("""SELECT tt.*,s.name AS sub_name,s.code,u.full_name AS teacher,c.name AS room
                   FROM timetable tt JOIN subjects s ON s.id=tt.subject_id
                   JOIN teachers te ON te.id=tt.teacher_id JOIN users u ON u.id=te.user_id
                   LEFT JOIN classrooms c ON c.id=tt.classroom_id
                   WHERE tt.department_id=%s AND tt.semester=%s
                   ORDER BY FIELD(tt.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),tt.start_time""",
                (stu['department_id'], stu['semester']))
    slots = cur.fetchall(); cur.close()
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    timetable = {d: [s for s in slots if s['day_of_week'] == d] for d in days}
    return render_template('student/timetable.html', stu=stu, timetable=timetable, days=days)

# ── Attendance ────────────────────────────────────────────────
@student_bp.route('/attendance')
@student_required
def attendance():
    stu = get_student(); db = get_db(); cur = db.cursor()
    
    # Subject-wise attendance summary
    cur.execute("""SELECT s.name AS sub_name, s.code,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END) AS late,
                          COUNT(*) AS total,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS pct
                   FROM attendance a JOIN subjects s ON s.id=a.subject_id
                   WHERE a.student_id=%s GROUP BY a.subject_id, s.name, s.code ORDER BY s.name""", (stu['id'],))
    subject_att = cur.fetchall()
    
    # Recent attendance records (last 50 for better calendar coverage)
    cur.execute("""SELECT a.date, s.name AS sub_name, s.code, a.status
                   FROM attendance a JOIN subjects s ON s.id=a.subject_id
                   WHERE a.student_id=%s ORDER BY a.date DESC LIMIT 50""", (stu['id'],))
    recent_att = cur.fetchall()
    
    # Monthly attendance trend (last 6 months) - simplified
    cur.execute("""SELECT DATE_FORMAT(a.date, '%%Y-%%m') AS month,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END) AS late,
                          COUNT(*) AS total
                   FROM attendance a
                   WHERE a.student_id=%s AND a.date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                   GROUP BY DATE_FORMAT(a.date, '%%Y-%%m')
                   ORDER BY month""", (stu['id'],))
    monthly_trend = cur.fetchall()
    
    # Weekly attendance pattern (which days have most absences)
    cur.execute("""SELECT DAYNAME(a.date) AS day_name,
                          DAYOFWEEK(a.date) AS day_num,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          COUNT(*) AS total
                   FROM attendance a
                   WHERE a.student_id=%s
                   GROUP BY DAYNAME(a.date), DAYOFWEEK(a.date)
                   ORDER BY day_num""", (stu['id'],))
    weekly_pattern = cur.fetchall()
    
    # Overall stats
    cur.execute("""SELECT COUNT(*) AS total_classes,
                          SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS total_present,
                          SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) AS total_absent,
                          SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) AS total_late,
                          ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS overall_pct
                   FROM attendance WHERE student_id=%s""", (stu['id'],))
    overall_stats = cur.fetchone()
    
    cur.close()
    return render_template('student/attendance_new.html', 
        stu=stu, 
        subject_att=subject_att if subject_att else [],
        recent_att=recent_att if recent_att else [],
        monthly_trend=monthly_trend if monthly_trend else [],
        weekly_pattern=weekly_pattern if weekly_pattern else [],
        overall_stats=overall_stats)

# ── Subjects & Results — from teacher_subjects (same as what teachers teach) ──
@student_bp.route('/subjects')
@student_required
def subjects():
    stu = get_student(); db = get_db(); cur = db.cursor()
    # Fetch subjects that have a teacher assigned in the student's dept + semester
    # This ensures the student sees exactly what their teachers are teaching
    cur.execute("""
        SELECT DISTINCT s.id,s.code,s.name,s.credits,s.subject_type,s.semester,s.year,
               u.full_name AS teacher_name, t.designation
        FROM subjects s
        JOIN teacher_subjects ts ON ts.subject_id = s.id
        JOIN teachers t ON t.id = ts.teacher_id
        JOIN users u ON u.id = t.user_id
        WHERE s.department_id = %s AND s.semester = %s
        ORDER BY s.code
    """, (stu['department_id'], stu['semester']))
    subjects = cur.fetchall()

    # If no teacher assigned yet, fall back to all subjects in dept+semester
    if not subjects:
        cur.execute("""SELECT s.*,'Not assigned' AS teacher_name,'' AS designation
                       FROM subjects s WHERE s.department_id=%s AND s.semester=%s ORDER BY s.code""",
                    (stu['department_id'], stu['semester']))
        subjects = cur.fetchall()

    # Results (Internal / External per subject)
    cur.execute("""
        SELECT s.id,s.code,s.name AS sub_name,
               MAX(CASE WHEN e.name='Internal' THEN m.marks_obtained END) AS internal_marks,
               MAX(CASE WHEN e.name='Internal' THEN e.max_marks END) AS internal_max,
               MAX(CASE WHEN e.name='External' THEN m.marks_obtained END) AS external_marks,
               MAX(CASE WHEN e.name='External' THEN e.max_marks END) AS external_max
        FROM subjects s
        LEFT JOIN exams e ON e.subject_id=s.id AND e.name IN ('Internal','External')
        LEFT JOIN marks m ON m.exam_id=e.id AND m.student_id=%s
        WHERE s.department_id=%s AND s.semester=%s
        GROUP BY s.id
        ORDER BY s.code
    """, (stu['id'], stu['department_id'], stu['semester']))
    results = cur.fetchall(); cur.close()
    return render_template('student/subjects.html', stu=stu, subjects=subjects, results=results)

# ── Fees ──────────────────────────────────────────────────────
@student_bp.route('/fees')
@student_required
def fees():
    stu = get_student(); db = get_db(); cur = db.cursor()
    cur.execute("""SELECT f.*,fc.name AS cat_name,ay.year_label
                   FROM fees f JOIN fee_categories fc ON fc.id=f.fee_category_id
                   LEFT JOIN academic_years ay ON ay.id=f.academic_year_id
                   WHERE f.student_id=%s ORDER BY f.due_date""", (stu['id'],))
    fees = cur.fetchall()
    cur.execute("""SELECT p.*,fc.name AS cat_name
                   FROM payments p JOIN fees f ON f.id=p.fee_id
                   JOIN fee_categories fc ON fc.id=f.fee_category_id
                   WHERE p.student_id=%s ORDER BY p.payment_date DESC""", (stu['id'],))
    payments = cur.fetchall(); cur.close()
    return render_template('student/fees.html', stu=stu, fees=fees, payments=payments)

# ── Assignments ───────────────────────────────────────────────
@student_bp.route('/assignments')
@student_required
def assignments():
    stu = get_student(); db = get_db(); cur = db.cursor()
    cur.execute("""SELECT a.*,s.name AS sub_name,u.full_name AS teacher,
                          sub.id AS sub_id,sub.status AS sub_status,
                          sub.marks_obtained,sub.submitted_at
                   FROM assignments a JOIN subjects s ON s.id=a.subject_id
                   JOIN teachers te ON te.id=a.teacher_id JOIN users u ON u.id=te.user_id
                   LEFT JOIN submissions sub ON sub.assignment_id=a.id AND sub.student_id=%s
                   WHERE a.department_id=%s AND a.semester=%s ORDER BY a.due_date""",
                (stu['id'], stu['department_id'], stu['semester']))
    assignments = cur.fetchall(); cur.close()
    return render_template('student/assignments.html', stu=stu, assignments=assignments)

@student_bp.route('/assignments/<int:aid>/submit', methods=['GET','POST'])
@student_required
def submit_assignment(aid):
    stu = get_student(); db = get_db(); cur = db.cursor()
    cur.execute("SELECT a.*,s.name AS sub_name FROM assignments a JOIN subjects s ON s.id=a.subject_id WHERE a.id=%s", (aid,))
    assignment = cur.fetchone()
    if request.method == 'POST':
        fname = save_file(request.files.get('file'), prefix=f'sub_{stu["id"]}_{aid}')
        if fname:
            cur.execute("""INSERT INTO submissions (assignment_id,student_id,file_path,status)
                           VALUES(%s,%s,%s,'Submitted')
                           ON DUPLICATE KEY UPDATE file_path=%s,submitted_at=NOW(),status='Submitted'""",
                        (aid, stu['id'], fname, fname))
            db.commit()
            flash('Assignment submitted!', 'success')
            return redirect(url_for('student.assignments'))
        else:
            flash('Invalid file type.', 'danger')
    cur.close()
    return render_template('student/submit_assignment.html', stu=stu, assignment=assignment)

# ── PYQ — subjects come from teacher_subjects for this dept+sem ──
@student_bp.route('/pyq')
@student_required
def pyq():
    stu = get_student()
    sem_filter = int(request.args.get('semester', stu['semester']))
    dept_code  = stu['dept_code']

    # Fetch subjects that are actually taught (from teacher_subjects)
    db = get_db(); cur = db.cursor()
    cur.execute("""
        SELECT DISTINCT s.id,s.code,s.name
        FROM subjects s
        JOIN teacher_subjects ts ON ts.subject_id = s.id
        WHERE s.department_id = %s AND s.semester = %s
        ORDER BY s.name
    """, (stu['department_id'], sem_filter))
    taught_subjects = cur.fetchall()

    # Fallback: all subjects if none assigned
    if not taught_subjects:
        cur.execute("""SELECT id,code,name FROM subjects
                       WHERE department_id=%s AND semester=%s ORDER BY name""",
                    (stu['department_id'], sem_filter))
        taught_subjects = cur.fetchall()

    # Local uploaded papers
    cur.execute("""SELECT p.*,s.name AS sub_name,s.code
                   FROM pyq_papers p JOIN subjects s ON s.id=p.subject_id
                   WHERE p.department_id=%s AND p.semester=%s
                   ORDER BY p.exam_year DESC,s.name""",
                (stu['department_id'], sem_filter))
    local_papers = cur.fetchall(); cur.close()

    # Online papers from MU website
    online_papers = fetch_pyq_papers(dept_code, sem_filter)
    source_url    = get_source_url(dept_code, sem_filter)

    return render_template('student/pyq.html',
        stu=stu, online_papers=online_papers, local_papers=local_papers,
        taught_subjects=taught_subjects, selected_sem=sem_filter, source_url=source_url,
        dept_code=dept_code)

# ── Profile ───────────────────────────────────────────────────
@student_bp.route('/profile')
@student_required
def profile():
    stu = get_student(); db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (current_user.id,)); user = cur.fetchone()
    cur.execute("SELECT * FROM documents WHERE user_id=%s ORDER BY uploaded_at DESC", (current_user.id,))
    docs = cur.fetchall(); cur.close()
    return render_template('student/profile.html', stu=stu, user=user, docs=docs)

@student_bp.route('/profile/upload-doc', methods=['POST'])
@student_required
def upload_doc():
    doc_type = request.form.get('doc_type', 'Other')
    fname = save_file(request.files.get('document'), prefix=f'doc_{current_user.id}')
    if fname:
        db = get_db(); cur = db.cursor()
        cur.execute("INSERT INTO documents (user_id,doc_type,file_path) VALUES(%s,%s,%s)",
                    (current_user.id, doc_type, fname))
        db.commit(); cur.close()
        flash('Document uploaded!', 'success')
    else:
        flash('Invalid file type.', 'danger')
    return redirect(url_for('student.profile'))
