-- Fix: assign demo teacher to Computer Engineering subjects (Sem 3)
-- Run: mysql -u root -p college_erp < utils/fix_teacher_subjects.sql

USE college_erp;

-- Find teacher id for sharma@college.edu
SET @tid = (SELECT t.id FROM teachers t JOIN users u ON u.id=t.user_id WHERE u.email='sharma@college.edu');
SET @ay  = (SELECT id FROM academic_years WHERE is_current=1 LIMIT 1);

-- Assign all COMP Sem 3 & 4 subjects to demo teacher
INSERT IGNORE INTO teacher_subjects (teacher_id, subject_id, academic_year_id)
SELECT @tid, s.id, @ay
FROM subjects s
WHERE s.department_id = (SELECT id FROM departments WHERE code='COMP')
  AND s.semester IN (3, 4);

SELECT CONCAT('Assigned ', ROW_COUNT(), ' subjects to demo teacher') AS result;
