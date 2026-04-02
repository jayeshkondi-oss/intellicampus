"""Admin blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from decimal import Decimal, InvalidOperation
import datetime
from db import get_db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ─────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM students"); total_students = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM teachers"); total_teachers = cur.fetchone()['cnt']
    cur.execute("SELECT COALESCE(SUM(amount_paid),0) AS total FROM payments WHERE MONTH(payment_date)=MONTH(CURDATE())")
    monthly_fee = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) AS cnt FROM fees WHERE status='Pending'"); pending_fees = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM leave_applications WHERE status='Pending'"); pending_leaves = cur.fetchone()['cnt']
    cur.execute("""SELECT d.name,d.code,COUNT(DISTINCT s.id) AS students,COUNT(DISTINCT t.id) AS teachers
                   FROM departments d
                   LEFT JOIN students s ON s.department_id=d.id
                   LEFT JOIN teachers t ON t.department_id=d.id
                   GROUP BY d.id ORDER BY d.name""")
    dept_stats = cur.fetchall()
    
    cur.execute("""SELECT DATE_FORMAT(payment_date, '%%b') AS month_name, COALESCE(SUM(amount_paid),0) AS total
                   FROM payments WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                   GROUP BY YEAR(payment_date), MONTH(payment_date), month_name
                   ORDER BY YEAR(payment_date), MONTH(payment_date)""")
    fee_trends = cur.fetchall()
    
    cur.close()
    return render_template('admin/dashboard.html',
        total_students=total_students, total_teachers=total_teachers,
        monthly_fee=monthly_fee, pending_fees=pending_fees,
        pending_leaves=pending_leaves, dept_stats=dept_stats, fee_trends=fee_trends)

def _generate_receipt_number():
    return datetime.datetime.now().strftime('RCP%Y%m%d%H%M%S%f')[:30]

def _refresh_fee_status(cur, fee_id):
    cur.execute("SELECT amount FROM fees WHERE id=%s", (fee_id,))
    fee = cur.fetchone()
    if not fee:
        return
    cur.execute("SELECT COALESCE(SUM(amount_paid),0) AS total_paid FROM payments WHERE fee_id=%s", (fee_id,))
    paid_row = cur.fetchone()
    total_paid = Decimal(str(paid_row['total_paid'] or 0))
    fee_amount = Decimal(str(fee['amount'] or 0))
    if total_paid <= 0:
        status = 'Pending'
    elif total_paid >= fee_amount:
        status = 'Paid'
    else:
        status = 'Partial'
    cur.execute("UPDATE fees SET status=%s WHERE id=%s", (status, fee_id))

@admin_bp.route('/fees', methods=['GET', 'POST'])
@admin_required
def fees():
    db = get_db(); cur = db.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'assign_fee':
                student_id = request.form.get('student_id')
                category_id = request.form.get('fee_category_id')
                academic_year_id = request.form.get('academic_year_id') or None
                due_date = request.form.get('due_date') or None
                amount_raw = (request.form.get('amount') or '').strip()

                if not student_id or not category_id:
                    raise ValueError('Student and fee category are required.')

                cur.execute("SELECT name, amount FROM fee_categories WHERE id=%s", (category_id,))
                category = cur.fetchone()
                if not category:
                    raise ValueError('Selected fee category was not found.')

                amount = Decimal(amount_raw) if amount_raw else Decimal(str(category['amount']))
                if amount <= 0:
                    raise ValueError('Fee amount must be greater than zero.')

                cur.execute("""INSERT INTO fees
                               (student_id, fee_category_id, academic_year_id, amount, due_date, status)
                               VALUES (%s,%s,%s,%s,%s,'Pending')""",
                            (student_id, category_id, academic_year_id, amount, due_date))
                db.commit()
                flash(f"{category['name']} fee assigned successfully.", 'success')

            elif action == 'record_payment':
                fee_id = request.form.get('fee_id')
                amount_paid_raw = (request.form.get('amount_paid') or '').strip()
                payment_mode = request.form.get('payment_mode') or 'Online'
                transaction_id = (request.form.get('transaction_id') or '').strip() or None
                receipt_number = (request.form.get('receipt_number') or '').strip() or _generate_receipt_number()
                payment_date_raw = request.form.get('payment_date') or None

                if not fee_id or not amount_paid_raw:
                    raise ValueError('Fee record and payment amount are required.')

                try:
                    amount_paid = Decimal(amount_paid_raw)
                except InvalidOperation as exc:
                    raise ValueError('Payment amount must be a valid number.') from exc
                if amount_paid <= 0:
                    raise ValueError('Payment amount must be greater than zero.')
                if payment_mode not in {'Online', 'Cash', 'DD', 'Cheque'}:
                    raise ValueError('Unsupported payment mode selected.')

                cur.execute("""SELECT f.id, f.student_id, f.amount, f.status, fc.name AS cat_name,
                                      u.full_name, s.roll_number,
                                      COALESCE(SUM(p.amount_paid),0) AS paid_total
                               FROM fees f
                               JOIN students s ON s.id=f.student_id
                               JOIN users u ON u.id=s.user_id
                               JOIN fee_categories fc ON fc.id=f.fee_category_id
                               LEFT JOIN payments p ON p.fee_id=f.id
                               WHERE f.id=%s
                               GROUP BY f.id, fc.name, u.full_name, s.roll_number""", (fee_id,))
                fee = cur.fetchone()
                if not fee:
                    raise ValueError('Selected fee record was not found.')
                if fee['status'] == 'Waived':
                    raise ValueError('Waived fee records cannot receive payments.')

                outstanding = Decimal(str(fee['amount'])) - Decimal(str(fee['paid_total'] or 0))
                if outstanding <= 0:
                    raise ValueError('Selected fee record has no outstanding balance.')
                if amount_paid > outstanding:
                    raise ValueError(f"Payment exceeds the outstanding balance of Rs. {outstanding:,.2f}.")

                payment_date = None
                if payment_date_raw:
                    payment_date = datetime.datetime.fromisoformat(payment_date_raw)

                if payment_date:
                    cur.execute("""INSERT INTO payments
                                   (fee_id, student_id, amount_paid, payment_date, payment_mode, transaction_id, receipt_number)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                                (fee['id'], fee['student_id'], amount_paid, payment_date,
                                 payment_mode, transaction_id, receipt_number))
                else:
                    cur.execute("""INSERT INTO payments
                                   (fee_id, student_id, amount_paid, payment_mode, transaction_id, receipt_number)
                                   VALUES (%s,%s,%s,%s,%s,%s)""",
                                (fee['id'], fee['student_id'], amount_paid,
                                 payment_mode, transaction_id, receipt_number))
                _refresh_fee_status(cur, fee['id'])
                db.commit()
                flash(f"Payment recorded for {fee['full_name']} ({fee['cat_name']}).", 'success')

            else:
                raise ValueError('Unsupported fee action.')

            return redirect(url_for('admin.fees'))
        except (ValueError, InvalidOperation) as e:
            db.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            db.rollback()
            flash(f'Unable to update fees: {str(e)}', 'danger')

    dept = request.args.get('dept', '')
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    search = request.args.get('q', '').strip()

    cur.execute("SELECT * FROM departments ORDER BY name"); depts = cur.fetchall()
    cur.execute("SELECT * FROM fee_categories ORDER BY name"); categories = cur.fetchall()
    cur.execute("SELECT * FROM academic_years ORDER BY is_current DESC, year_label DESC"); academic_years = cur.fetchall()
    cur.execute("""SELECT s.id, s.roll_number, u.full_name, d.code AS dept_code
                   FROM students s
                   JOIN users u ON u.id=s.user_id
                   JOIN departments d ON d.id=s.department_id
                   ORDER BY s.roll_number, u.full_name""")
    students = cur.fetchall()

    fee_query = """SELECT f.id, f.student_id, f.fee_category_id, f.amount, f.due_date, f.status,
                          u.full_name, s.roll_number, d.name AS dept_name, d.code AS dept_code,
                          fc.name AS cat_name, ay.year_label,
                          COALESCE(SUM(p.amount_paid),0) AS paid_amount,
                          GREATEST(f.amount - COALESCE(SUM(p.amount_paid),0),0) AS balance
                   FROM fees f
                   JOIN students s ON s.id=f.student_id
                   JOIN users u ON u.id=s.user_id
                   JOIN departments d ON d.id=s.department_id
                   JOIN fee_categories fc ON fc.id=f.fee_category_id
                   LEFT JOIN academic_years ay ON ay.id=f.academic_year_id
                   LEFT JOIN payments p ON p.fee_id=f.id
                   WHERE 1=1"""
    fee_params = []
    if dept:
        fee_query += " AND s.department_id=%s"; fee_params.append(dept)
    if status:
        fee_query += " AND f.status=%s"; fee_params.append(status)
    if category:
        fee_query += " AND f.fee_category_id=%s"; fee_params.append(category)
    if search:
        fee_query += " AND (u.full_name LIKE %s OR s.roll_number LIKE %s)"
        fee_params += [f'%{search}%', f'%{search}%']
    fee_query += """ GROUP BY f.id, u.full_name, s.roll_number, d.name, d.code, fc.name, ay.year_label
                     ORDER BY FIELD(f.status,'Pending','Partial','Paid','Waived'),
                              f.due_date IS NULL, f.due_date, u.full_name"""
    cur.execute(fee_query, fee_params)
    fee_rows = cur.fetchall()

    payment_query = """SELECT p.id, p.amount_paid, p.payment_date, p.payment_mode, p.receipt_number, p.transaction_id,
                              u.full_name, s.roll_number, d.code AS dept_code, fc.name AS cat_name, f.status AS fee_status
                       FROM payments p
                       JOIN fees f ON f.id=p.fee_id
                       JOIN students s ON s.id=p.student_id
                       JOIN users u ON u.id=s.user_id
                       JOIN departments d ON d.id=s.department_id
                       JOIN fee_categories fc ON fc.id=f.fee_category_id
                       WHERE 1=1"""
    payment_params = []
    if dept:
        payment_query += " AND s.department_id=%s"; payment_params.append(dept)
    if status:
        payment_query += " AND f.status=%s"; payment_params.append(status)
    if category:
        payment_query += " AND f.fee_category_id=%s"; payment_params.append(category)
    if search:
        payment_query += " AND (u.full_name LIKE %s OR s.roll_number LIKE %s)"
        payment_params += [f'%{search}%', f'%{search}%']
    payment_query += " ORDER BY p.payment_date DESC LIMIT 20"
    cur.execute(payment_query, payment_params)
    payments = cur.fetchall()

    cur.execute("""SELECT f.id, u.full_name, s.roll_number, fc.name AS cat_name,
                          f.amount, COALESCE(SUM(p.amount_paid),0) AS paid_amount,
                          GREATEST(f.amount - COALESCE(SUM(p.amount_paid),0),0) AS balance
                   FROM fees f
                   JOIN students s ON s.id=f.student_id
                   JOIN users u ON u.id=s.user_id
                   JOIN fee_categories fc ON fc.id=f.fee_category_id
                   LEFT JOIN payments p ON p.fee_id=f.id
                   WHERE f.status IN ('Pending','Partial')
                   GROUP BY f.id, u.full_name, s.roll_number, fc.name
                   HAVING balance > 0
                   ORDER BY u.full_name, s.roll_number, f.due_date IS NULL, f.due_date""")
    payable_fees = cur.fetchall()

    pending_amount = sum(Decimal(str(row['balance'] or 0)) for row in fee_rows if row['status'] in ('Pending', 'Partial'))
    collected_amount = sum(Decimal(str(row['paid_amount'] or 0)) for row in fee_rows)
    pending_records = sum(1 for row in fee_rows if row['status'] in ('Pending', 'Partial'))
    total_records = len(fee_rows)

    cur.close()
    return render_template('admin/fees.html',
                           fee_rows=fee_rows, payments=payments, students=students,
                           categories=categories, academic_years=academic_years,
                           payable_fees=payable_fees, depts=depts,
                           filters={'dept': dept, 'status': status, 'category': category, 'q': search},
                           pending_amount=pending_amount, collected_amount=collected_amount,
                           pending_records=pending_records, total_records=total_records)

# ── Student Management ────────────────────────────────────────
@admin_bp.route('/students')
@admin_required
def students():
    dept=request.args.get('dept',''); year=request.args.get('year','')
    sem=request.args.get('semester',''); search=request.args.get('q','')
    db = get_db(); cur = db.cursor()
    q = """SELECT u.id AS uid,u.full_name,u.email,u.phone,u.is_active,
                  s.id AS sid,s.roll_number,s.year,s.semester,s.section,d.name AS dept_name
           FROM students s JOIN users u ON u.id=s.user_id
           JOIN departments d ON d.id=s.department_id WHERE 1=1"""
    params = []
    if dept:   q += " AND s.department_id=%s"; params.append(dept)
    if year:   q += " AND s.year=%s";          params.append(year)
    if sem:    q += " AND s.semester=%s";       params.append(sem)
    if search: q += " AND (u.full_name LIKE %s OR s.roll_number LIKE %s)"; params+=[f'%{search}%',f'%{search}%']
    q += " ORDER BY s.roll_number"
    cur.execute(q, params); students = cur.fetchall()
    cur.execute("SELECT * FROM departments"); depts = cur.fetchall()
    cur.close()
    return render_template('admin/students.html', students=students, depts=depts,
                           filters={'dept':dept,'year':year,'semester':sem,'q':search})

@admin_bp.route('/students/add', methods=['GET','POST'])
@admin_required
def add_student():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM departments"); depts = cur.fetchall()
    cur.execute("SELECT * FROM academic_years ORDER BY is_current DESC"); academic_years = cur.fetchall()
    error = None
    if request.method == 'POST':
        f = request.form
        try:
            pw_hash = generate_password_hash(f['password'])
            cur.execute("INSERT INTO users (email,password_hash,role,full_name,phone) VALUES(%s,%s,'student',%s,%s)",
                        (f['email'],pw_hash,f['full_name'],f.get('phone','')))
            uid = cur.lastrowid
            cur.execute("""INSERT INTO students
                (user_id,roll_number,department_id,year,semester,section,dob,gender,
                 address,guardian_name,guardian_phone,admission_year,academic_year_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (uid,f['roll_number'],f['department_id'],f['year'],f['semester'],
                 f.get('section','A'),f.get('dob') or None,f.get('gender') or None,
                 f.get('address'),f.get('guardian_name'),f.get('guardian_phone'),
                 f.get('admission_year') or None,f.get('academic_year_id') or None))
            db.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.rollback(); error = str(e)
        finally:
            cur.close()
    return render_template('admin/add_student.html', depts=depts, academic_years=academic_years, error=error)

@admin_bp.route('/students/<int:sid>/edit', methods=['GET','POST'])
@admin_required
def edit_student(sid):
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.id AS uid,u.full_name,u.email,u.phone,u.is_active,
                          s.id AS sid,s.roll_number,s.department_id,s.year,s.semester,s.section,
                          s.dob,s.gender,s.address,s.guardian_name,s.guardian_phone,
                          s.admission_year,s.academic_year_id,
                          d.name AS dept_name
                   FROM students s JOIN users u ON u.id=s.user_id
                   JOIN departments d ON d.id=s.department_id
                   WHERE s.id=%s""", (sid,))
    student = cur.fetchone()
    if not student:
        flash('Student not found.', 'danger')
        cur.close()
        return redirect(url_for('admin.students'))

    cur.execute("SELECT * FROM departments ORDER BY name"); depts = cur.fetchall()
    cur.execute("SELECT * FROM academic_years ORDER BY is_current DESC"); academic_years = cur.fetchall()
    error = None

    if request.method == 'POST':
        f = request.form
        try:
            update_fields = "full_name=%s, email=%s, phone=%s"
            params = [f['full_name'], f['email'], f.get('phone','')]
            if f.get('password'):
                update_fields += ", password_hash=%s"
                params.append(generate_password_hash(f['password']))
            params.append(student['uid'])
            cur.execute(f"UPDATE users SET {update_fields} WHERE id=%s", params)

            cur.execute("""UPDATE students SET roll_number=%s, department_id=%s, year=%s, semester=%s, section=%s,
                           dob=%s, gender=%s, address=%s, guardian_name=%s, guardian_phone=%s,
                           admission_year=%s, academic_year_id=%s WHERE id=%s""",
                        (f['roll_number'], f['department_id'], f['year'], f['semester'], f.get('section','A'),
                         f.get('dob') or None, f.get('gender') or None, f.get('address'),
                         f.get('guardian_name'), f.get('guardian_phone'),
                         f.get('admission_year') or None, f.get('academic_year_id') or None, sid))
            db.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.rollback(); error = str(e)
        finally:
            cur.close()

    else:
        cur.close()

    return render_template('admin/edit_student.html',
                           student=student, depts=depts,
                           academic_years=academic_years, error=error)

@admin_bp.route('/students/<int:sid>/toggle', methods=['POST'])
@admin_required
def toggle_student(sid):
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE users u JOIN students s ON s.user_id=u.id SET u.is_active=1-u.is_active WHERE s.id=%s",(sid,))
    db.commit(); cur.close()
    return jsonify({'ok': True})

@admin_bp.route('/students/<int:sid>/delete', methods=['POST'])
@admin_required
def delete_student(sid):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT user_id FROM students WHERE id=%s", (sid,))
    row = cur.fetchone()
    if row:
        try:
            for tbl, col in [('messages', 'sender_id'), ('messages', 'receiver_id'), ('notifications', 'created_by'), ('pyq_papers', 'uploaded_by')]:
                try:
                    if col == 'uploaded_by' or col == 'created_by':
                        cur.execute(f"UPDATE {tbl} SET {col}=NULL WHERE {col}=%s", (row['user_id'],))
                    else:
                        cur.execute(f"DELETE FROM {tbl} WHERE {col}=%s", (row['user_id'],))
                except Exception:
                    pass

            cur.execute("DELETE FROM users WHERE id=%s", (row['user_id'],))
            db.commit()
            flash('Student deleted successfully.', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error deleting student: {str(e)}', 'danger')
    else:
        flash('Student not found.', 'danger')
    cur.close()
    return redirect(url_for('admin.students'))

# ── Faculty Management ────────────────────────────────────────
@admin_bp.route('/faculty')
@admin_required
def faculty():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.id AS uid,u.full_name,u.email,u.phone,u.is_active,
                          t.id AS tid,t.employee_id,t.designation,t.qualification,
                          t.department_id,d.name AS dept_name,
                          COUNT(DISTINCT ts.subject_id) AS subject_count
                   FROM teachers t JOIN users u ON u.id=t.user_id
                   JOIN departments d ON d.id=t.department_id
                   LEFT JOIN teacher_subjects ts ON ts.teacher_id=t.id
                   GROUP BY t.id ORDER BY u.full_name""")
    faculty = cur.fetchall(); cur.close()
    return render_template('admin/faculty.html', faculty=faculty)

def _get_subjects_for_form(cur):
    cur.execute("""SELECT s.*,d.name AS dept_name FROM subjects s
                   JOIN departments d ON d.id=s.department_id
                   ORDER BY s.department_id,s.year,s.semester,s.name""")
    return cur.fetchall()

@admin_bp.route('/faculty/add', methods=['GET','POST'])
@admin_required
def add_faculty():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM departments ORDER BY name"); depts = cur.fetchall()
    subjects = _get_subjects_for_form(cur)
    cur.execute("SELECT * FROM academic_years WHERE is_current=1"); ay = cur.fetchone()
    error = None
    if request.method == 'POST':
        f = request.form
        subject_ids = request.form.getlist('subject_ids')
        try:
            pw_hash = generate_password_hash(f['password'])
            cur.execute("INSERT INTO users (email,password_hash,role,full_name,phone) VALUES(%s,%s,'teacher',%s,%s)",
                        (f['email'],pw_hash,f['full_name'],f.get('phone','')))
            uid = cur.lastrowid
            cur.execute("""INSERT INTO teachers
                (user_id,employee_id,department_id,designation,qualification,joining_date,specialization)
                VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (uid,f['employee_id'],f['department_id'],f.get('designation'),
                 f.get('qualification'),f.get('joining_date') or None,f.get('specialization')))
            teacher_id = cur.lastrowid
            ay_id = ay['id'] if ay else None
            for sid in subject_ids:
                cur.execute("INSERT IGNORE INTO teacher_subjects (teacher_id,subject_id,academic_year_id) VALUES(%s,%s,%s)",
                            (teacher_id, sid, ay_id))
            db.commit()
            flash(f'Faculty added with {len(subject_ids)} subject(s) assigned!', 'success')
            return redirect(url_for('admin.faculty'))
        except Exception as e:
            db.rollback(); error = str(e)
        finally:
            cur.close()
    return render_template('admin/add_faculty.html', depts=depts, subjects=subjects, error=error)

@admin_bp.route('/faculty/<int:tid>/edit', methods=['GET','POST'])
@admin_required
def edit_faculty(tid):
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT u.*,t.*,d.name AS dept_name FROM users u
                   JOIN teachers t ON t.user_id=u.id
                   JOIN departments d ON d.id=t.department_id
                   WHERE t.id=%s""", (tid,))
    faculty = cur.fetchone()
    if not faculty:
        flash('Faculty not found.', 'danger')
        return redirect(url_for('admin.faculty'))

    cur.execute("SELECT * FROM departments ORDER BY name"); depts = cur.fetchall()
    subjects = _get_subjects_for_form(cur)
    cur.execute("SELECT subject_id FROM teacher_subjects WHERE teacher_id=%s", (tid,))
    assigned_ids = {row['subject_id'] for row in cur.fetchall()}
    cur.execute("SELECT * FROM academic_years WHERE is_current=1"); ay = cur.fetchone()
    error = success = None

    if request.method == 'POST':
        f = request.form
        subject_ids = request.form.getlist('subject_ids')
        try:
            from werkzeug.security import generate_password_hash
            update_fields = "full_name=%s, email=%s, phone=%s"
            params = [f['full_name'], f['email'], f.get('phone','')]
            if f.get('password'):
                update_fields += ", password_hash=%s"
                params.append(generate_password_hash(f['password']))
            params.append(faculty['id'])  # user id
            cur.execute(f"UPDATE users SET {update_fields} WHERE id=%s", params)

            cur.execute("""UPDATE teachers SET employee_id=%s, department_id=%s, designation=%s,
                           qualification=%s, joining_date=%s, specialization=%s WHERE id=%s""",
                        (f['employee_id'],f['department_id'],f.get('designation'),
                         f.get('qualification'),f.get('joining_date') or None,
                         f.get('specialization'),tid))

            # Update subject assignments: delete old, insert new
            cur.execute("DELETE FROM teacher_subjects WHERE teacher_id=%s", (tid,))
            ay_id = ay['id'] if ay else None
            for sid in subject_ids:
                cur.execute("INSERT IGNORE INTO teacher_subjects (teacher_id,subject_id,academic_year_id) VALUES(%s,%s,%s)",
                            (tid, sid, ay_id))
            db.commit()
            flash(f'Faculty updated with {len(subject_ids)} subject(s)!', 'success')
            return redirect(url_for('admin.faculty'))
        except Exception as e:
            db.rollback(); error = str(e)
        finally:
            cur.close()

    return render_template('admin/edit_faculty.html',
        faculty=faculty, depts=depts, subjects=subjects,
        assigned_ids=assigned_ids, error=error, success=success)

@admin_bp.route('/faculty/<int:tid>/delete', methods=['POST'])
@admin_required
def delete_faculty(tid):
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT user_id FROM teachers WHERE id=%s", (tid,))
    row = cur.fetchone()
    if row:
        uid = row['user_id']
        try:
            # Manually clean up uncascaded foreign keys referencing teachers
            try: cur.execute("DELETE FROM teacher_subjects WHERE teacher_id=%s", (tid,))
            except Exception: pass
            try: cur.execute("DELETE FROM timetable WHERE teacher_id=%s", (tid,))
            except Exception: pass
            try: cur.execute("DELETE FROM attendance WHERE teacher_id=%s", (tid,))
            except Exception: pass
            try: cur.execute("DELETE FROM assignments WHERE teacher_id=%s", (tid,))
            except Exception: pass
            try: cur.execute("UPDATE marks SET entered_by=NULL WHERE entered_by=%s", (tid,))
            except Exception: pass
            try: cur.execute("DELETE FROM leave_applications WHERE teacher_id=%s", (tid,))
            except Exception: pass
            
            # Clean up user-level references
            try: cur.execute("DELETE FROM messages WHERE sender_id=%s OR receiver_id=%s", (uid, uid))
            except Exception: pass
            try: cur.execute("UPDATE notifications SET created_by=NULL WHERE created_by=%s", (uid,))
            except Exception: pass
            try: cur.execute("UPDATE pyq_papers SET uploaded_by=NULL WHERE uploaded_by=%s", (uid,))
            except Exception: pass
            
            # Deleting the user automatically deletes the mapped teacher record
            cur.execute("DELETE FROM users WHERE id=%s", (uid,))
            db.commit()
            flash('Faculty deleted successfully.', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error deleting faculty: {str(e)}', 'danger')
    else:
        flash('Faculty not found.', 'danger')
    cur.close()
    return redirect(url_for('admin.faculty'))

# ── Timetable ─────────────────────────────────────────────────
@admin_bp.route('/timetable')
@admin_required
def timetable():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT t.*,s.name AS sub_name,s.code AS sub_code,
                          u.full_name AS teacher_name,d.name AS dept_name,c.name AS room
                   FROM timetable t JOIN subjects s ON s.id=t.subject_id
                   JOIN teachers te ON te.id=t.teacher_id JOIN users u ON u.id=te.user_id
                   JOIN departments d ON d.id=t.department_id
                   LEFT JOIN classrooms c ON c.id=t.classroom_id
                   ORDER BY FIELD(t.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'),t.start_time""")
    slots = cur.fetchall()
    cur.execute("SELECT * FROM departments"); depts = cur.fetchall()
    cur.close()
    return render_template('admin/timetable.html', slots=slots, depts=depts)

@admin_bp.route('/timetable/add', methods=['GET','POST'])
@admin_required
def add_timetable():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT s.*,d.code FROM subjects s JOIN departments d ON d.id=s.department_id"); subjects = cur.fetchall()
    cur.execute("SELECT t.*,u.full_name FROM teachers t JOIN users u ON u.id=t.user_id"); teachers = cur.fetchall()
    cur.execute("SELECT * FROM classrooms"); classrooms = cur.fetchall()
    cur.execute("SELECT * FROM departments"); depts = cur.fetchall()
    cur.execute("SELECT * FROM academic_years WHERE is_current=1"); ay = cur.fetchone()
    error = None
    if request.method == 'POST':
        f = request.form
        try:
            cur.execute("""INSERT INTO timetable
                (subject_id,teacher_id,classroom_id,department_id,semester,section,
                 day_of_week,start_time,end_time,academic_year_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (f['subject_id'],f['teacher_id'],f.get('classroom_id') or None,
                 f['department_id'],f['semester'],f.get('section','A'),
                 f['day_of_week'],f['start_time'],f['end_time'],ay['id'] if ay else None))
            db.commit()
            flash('Timetable slot added!', 'success')
            return redirect(url_for('admin.timetable'))
        except Exception as e:
            db.rollback(); error = str(e)
        finally:
            cur.close()
    return render_template('admin/add_timetable.html',
        subjects=subjects,teachers=teachers,classrooms=classrooms,depts=depts,error=error)

# ── Attendance ────────────────────────────────────────────────
@admin_bp.route('/attendance')
@admin_required
def attendance():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT d.name AS dept,s.name AS sub,
                          SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                          SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
                          COUNT(*) AS total
                   FROM attendance a JOIN subjects s ON s.id=a.subject_id
                   JOIN departments d ON d.id=s.department_id
                   WHERE a.date >= DATE_SUB(CURDATE(),INTERVAL 30 DAY)
                   GROUP BY d.id,s.id,d.name,s.name ORDER BY d.name,s.name""")
    att_summary = cur.fetchall()
    cur.execute("""SELECT u.full_name,s2.roll_number,d.name AS dept,sub.name AS sub_name,
                          ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS pct
                   FROM attendance a JOIN students s2 ON s2.id=a.student_id
                   JOIN users u ON u.id=s2.user_id JOIN departments d ON d.id=s2.department_id
                   JOIN subjects sub ON sub.id=a.subject_id
                   GROUP BY a.student_id,a.subject_id,u.full_name,s2.roll_number,d.name,sub.name 
                   HAVING pct < 75 ORDER BY pct""")
    defaulters = cur.fetchall(); cur.close()
    return render_template('admin/attendance.html', att_summary=att_summary, defaulters=defaulters)

# ── Leaves ────────────────────────────────────────────────────
@admin_bp.route('/leaves')
@admin_required
def leaves():
    db = get_db(); cur = db.cursor()
    cur.execute("""SELECT l.*,u.full_name,d.name AS dept
                   FROM leave_applications l JOIN teachers t ON t.id=l.teacher_id
                   JOIN users u ON u.id=t.user_id JOIN departments d ON d.id=t.department_id
                   ORDER BY l.applied_at DESC""")
    leaves = cur.fetchall(); cur.close()
    return render_template('admin/leaves.html', leaves=leaves)

@admin_bp.route('/leaves/<int:lid>/approve', methods=['POST'])
@admin_required
def approve_leave(lid):
    action = request.form.get('action','Approved')
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE leave_applications SET status=%s,reviewed_by=%s WHERE id=%s",(action,current_user.id,lid))
    db.commit(); cur.close()
    return redirect(url_for('admin.leaves'))
