-- ============================================================
--  College ERP System — MySQL Schema
--  Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE TABLE departments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    code       VARCHAR(10)  NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE academic_years (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    year_label VARCHAR(20) NOT NULL,
    is_current TINYINT(1) DEFAULT 0
);

CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','teacher','student') NOT NULL,
    full_name     VARCHAR(120) NOT NULL,
    phone         VARCHAR(15),
    avatar        VARCHAR(255),
    is_active     TINYINT(1) DEFAULT 1,
    last_login    DATETIME,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL UNIQUE,
    roll_number      VARCHAR(20) NOT NULL UNIQUE,
    department_id    INT NOT NULL,
    year             TINYINT NOT NULL,
    semester         TINYINT NOT NULL,
    section          VARCHAR(5) DEFAULT 'A',
    dob              DATE,
    gender           ENUM('Male','Female','Other'),
    address          TEXT,
    guardian_name    VARCHAR(120),
    guardian_phone   VARCHAR(15),
    admission_year   YEAR,
    academic_year_id INT,
    FOREIGN KEY (user_id)          REFERENCES users(id)          ON DELETE CASCADE,
    FOREIGN KEY (department_id)    REFERENCES departments(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE TABLE teachers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL UNIQUE,
    employee_id     VARCHAR(20) NOT NULL UNIQUE,
    department_id   INT NOT NULL,
    designation     VARCHAR(80),
    qualification   VARCHAR(120),
    joining_date    DATE,
    specialization  VARCHAR(120),
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE subjects (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    code          VARCHAR(20) NOT NULL UNIQUE,
    name          VARCHAR(120) NOT NULL,
    department_id INT NOT NULL,
    semester      TINYINT NOT NULL,
    year          TINYINT NOT NULL,
    credits       TINYINT DEFAULT 3,
    subject_type  ENUM('Theory','Practical','Elective') DEFAULT 'Theory',
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE teacher_subjects (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id       INT NOT NULL,
    subject_id       INT NOT NULL,
    academic_year_id INT,
    UNIQUE KEY uniq_ts (teacher_id, subject_id, academic_year_id),
    FOREIGN KEY (teacher_id)       REFERENCES teachers(id)       ON DELETE CASCADE,
    FOREIGN KEY (subject_id)       REFERENCES subjects(id)       ON DELETE CASCADE,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE TABLE classrooms (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(50) NOT NULL,
    capacity SMALLINT,
    building VARCHAR(50)
);

CREATE TABLE timetable (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    subject_id       INT NOT NULL,
    teacher_id       INT NOT NULL,
    classroom_id     INT,
    department_id    INT NOT NULL,
    semester         TINYINT NOT NULL,
    section          VARCHAR(5) DEFAULT 'A',
    day_of_week      ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
    start_time       TIME NOT NULL,
    end_time         TIME NOT NULL,
    academic_year_id INT,
    FOREIGN KEY (subject_id)       REFERENCES subjects(id),
    FOREIGN KEY (teacher_id)       REFERENCES teachers(id),
    FOREIGN KEY (classroom_id)     REFERENCES classrooms(id),
    FOREIGN KEY (department_id)    REFERENCES departments(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE TABLE attendance (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    date       DATE NOT NULL,
    status     ENUM('Present','Absent','Late') NOT NULL,
    remarks    VARCHAR(255),
    UNIQUE KEY uniq_att (student_id, subject_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

CREATE TABLE assignments (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    description   TEXT,
    subject_id    INT NOT NULL,
    teacher_id    INT NOT NULL,
    semester      TINYINT NOT NULL,
    department_id INT NOT NULL,
    due_date      DATETIME NOT NULL,
    max_marks     DECIMAL(5,2) DEFAULT 10,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id)    REFERENCES subjects(id),
    FOREIGN KEY (teacher_id)    REFERENCES teachers(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE submissions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id  INT NOT NULL,
    student_id     INT NOT NULL,
    file_path      VARCHAR(255),
    submitted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    marks_obtained DECIMAL(5,2),
    feedback       TEXT,
    status         ENUM('Submitted','Graded','Late') DEFAULT 'Submitted',
    UNIQUE KEY uniq_sub (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES students(id)   ON DELETE CASCADE
);

CREATE TABLE exams (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    subject_id       INT NOT NULL,
    department_id    INT NOT NULL,
    semester         TINYINT NOT NULL,
    exam_date        DATE,
    max_marks        DECIMAL(5,2),
    academic_year_id INT,
    FOREIGN KEY (subject_id)       REFERENCES subjects(id),
    FOREIGN KEY (department_id)    REFERENCES departments(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE TABLE marks (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    exam_id        INT NOT NULL,
    student_id     INT NOT NULL,
    marks_obtained DECIMAL(5,2),
    grade          VARCHAR(5),
    remarks        VARCHAR(255),
    entered_by     INT,
    UNIQUE KEY uniq_marks (exam_id, student_id),
    FOREIGN KEY (exam_id)    REFERENCES exams(id)    ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (entered_by) REFERENCES teachers(id)
);

CREATE TABLE fee_categories (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    name   VARCHAR(80) NOT NULL,
    amount DECIMAL(10,2) NOT NULL
);

CREATE TABLE fees (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    student_id       INT NOT NULL,
    fee_category_id  INT NOT NULL,
    academic_year_id INT,
    amount           DECIMAL(10,2) NOT NULL,
    due_date         DATE,
    status           ENUM('Pending','Paid','Partial','Waived') DEFAULT 'Pending',
    FOREIGN KEY (student_id)      REFERENCES students(id)       ON DELETE CASCADE,
    FOREIGN KEY (fee_category_id) REFERENCES fee_categories(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE TABLE payments (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    fee_id         INT NOT NULL,
    student_id     INT NOT NULL,
    amount_paid    DECIMAL(10,2) NOT NULL,
    payment_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_mode   ENUM('Online','Cash','DD','Cheque') DEFAULT 'Online',
    transaction_id VARCHAR(80),
    receipt_number VARCHAR(30) UNIQUE,
    FOREIGN KEY (fee_id)     REFERENCES fees(id)     ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE pyq_papers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    subject_id    INT NOT NULL,
    department_id INT NOT NULL,
    semester      TINYINT NOT NULL,
    exam_year     YEAR NOT NULL,
    exam_type     VARCHAR(50),
    file_path     VARCHAR(255),
    uploaded_by   INT,
    uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id)    REFERENCES subjects(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (uploaded_by)   REFERENCES users(id)
);

CREATE TABLE documents (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    doc_type    VARCHAR(80),
    file_path   VARCHAR(255),
    verified    TINYINT(1) DEFAULT 0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE leave_applications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id  INT NOT NULL,
    from_date   DATE NOT NULL,
    to_date     DATE NOT NULL,
    reason      TEXT,
    status      ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT,
    FOREIGN KEY (teacher_id)  REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

-- ─── SEED DATA ───
INSERT INTO departments (name, code) VALUES
  ('Computer Engineering','COMP'),('Information Technology','IT'),
  ('Electronics & Telecom','ENTC'),('Mechanical Engineering','MECH'),
  ('AI & Machine Learning','AIML'),('Data Science','DATA');

INSERT INTO academic_years (year_label, is_current) VALUES
  ('2022-23',0),('2023-24',0),('2024-25',1);

INSERT INTO fee_categories (name, amount) VALUES
  ('Tuition Fee',65000.00),('Development Fee',8000.00),
  ('Library Fee',2500.00),('Lab Fee',5000.00),('Hostel Fee',48000.00);

INSERT INTO classrooms (name, capacity, building) VALUES
  ('A-101',60,'A Block'),('A-102',60,'A Block'),
  ('B-201',80,'B Block'),('Lab-1',30,'Lab Block'),('Lab-2',30,'Lab Block');
