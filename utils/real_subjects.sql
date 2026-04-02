-- ================================================================
--  REAL SUBJECTS — Mumbai University BE Engineering
--  Run: mysql -u root -p college_erp < utils/real_subjects.sql
-- ================================================================
USE college_erp;

-- Disable FK checks so we can clear all tables safely
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE teacher_subjects;
TRUNCATE TABLE attendance;
TRUNCATE TABLE submissions;
TRUNCATE TABLE marks;
TRUNCATE TABLE assignments;
TRUNCATE TABLE timetable;
TRUNCATE TABLE subjects;

SET FOREIGN_KEY_CHECKS = 1;

-- ================================================================
--  DEPT 1 — COMPUTER ENGINEERING (COMP)
-- ================================================================

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC101','Engineering Mathematics I',1,1,1,4,'Theory'),
('CSC102','Engineering Physics',1,1,1,4,'Theory'),
('CSC103','Engineering Chemistry',1,1,1,4,'Theory'),
('CSC104','Engineering Mechanics',1,1,1,4,'Theory'),
('CSC105','Basic Electrical & Electronics Engg',1,1,1,4,'Theory'),
('CSL101','Engineering Physics Lab',1,1,1,2,'Practical'),
('CSL102','Engineering Chemistry Lab',1,1,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC201','Engineering Mathematics II',1,2,1,4,'Theory'),
('CSC202','Programming & Problem Solving',1,2,1,4,'Theory'),
('CSC203','Engineering Drawing',1,2,1,4,'Theory'),
('CSC204','Environmental Studies',1,2,1,3,'Theory'),
('CSC205','Communication Skills',1,2,1,3,'Theory'),
('CSL201','Programming Lab',1,2,1,2,'Practical'),
('CSL202','Engineering Drawing Lab',1,2,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC301','Engineering Mathematics III',1,3,2,4,'Theory'),
('CSC302','Data Structures',1,3,2,4,'Theory'),
('CSC303','Digital Logic & Computer Architecture',1,3,2,4,'Theory'),
('CSC304','Discrete Mathematics & Graph Theory',1,3,2,4,'Theory'),
('CSC305','Computer Graphics',1,3,2,4,'Theory'),
('CSL301','Data Structures Lab',1,3,2,2,'Practical'),
('CSL302','Computer Graphics Lab',1,3,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC401','Engineering Mathematics IV',1,4,2,4,'Theory'),
('CSC402','Analysis of Algorithms',1,4,2,4,'Theory'),
('CSC403','Database Management Systems',1,4,2,4,'Theory'),
('CSC404','Operating System',1,4,2,4,'Theory'),
('CSC405','Theory of Computation',1,4,2,4,'Theory'),
('CSL401','DBMS Lab',1,4,2,2,'Practical'),
('CSL402','Operating System Lab',1,4,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC501','Theoretical Computer Science',1,5,3,3,'Theory'),
('CSC502','Software Engineering',1,5,3,3,'Theory'),
('CSC503','Computer Network',1,5,3,3,'Theory'),
('CSC504','Data Warehousing & Mining',1,5,3,3,'Theory'),
('CSDLO5011','Probabilistic Graphical Models',1,5,3,3,'Elective'),
('CSDLO5012','Internet Programming',1,5,3,3,'Elective'),
('CSDLO5013','Advance Database Management System',1,5,3,3,'Elective'),
('CSL501','Software Engineering Lab',1,5,3,1,'Practical'),
('CSL502','Computer Network Lab',1,5,3,1,'Practical'),
('CSL503','Data Warehousing & Mining Lab',1,5,3,1,'Practical'),
('CSL504','Business Communication & Ethics II',1,5,3,2,'Practical'),
('CSM501','Mini Project: 2A',1,5,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC601','System Programming & Compiler Construction',1,6,3,3,'Theory'),
('CSC602','Cryptography & System Security',1,6,3,3,'Theory'),
('CSC603','Mobile Computing',1,6,3,3,'Theory'),
('CSC604','Artificial Intelligence',1,6,3,3,'Theory'),
('CSDLO6011','Internet of Things',1,6,3,3,'Elective'),
('CSDLO6012','Digital Signal & Image Processing',1,6,3,3,'Elective'),
('CSDLO6013','Quantitative Analysis',1,6,3,3,'Elective'),
('CSL601','System Programming & Compiler Construction Lab',1,6,3,1,'Practical'),
('CSL602','Cryptography & System Security Lab',1,6,3,1,'Practical'),
('CSL603','Mobile Computing Lab',1,6,3,1,'Practical'),
('CSL604','Artificial Intelligence Lab',1,6,3,1,'Practical'),
('CSL605','Skill base Lab Course: Cloud Computing',1,6,3,2,'Practical'),
('CSM601','Mini Project Lab: 2B',1,6,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC701','Machine Learning',1,7,4,3,'Theory'),
('CSC702','Big Data Analytics',1,7,4,3,'Theory'),
('CSDC701','Department Level Optional Course-3',1,7,4,3,'Elective'),
('CSDC702','Department Level Optional Course-4',1,7,4,3,'Elective'),
('CILO701','Institute Level Optional Course-1',1,7,4,3,'Elective'),
('CSL701','Machine Learning Lab',1,7,4,1,'Practical'),
('CSL702','Big Data Analytics Lab',1,7,4,1,'Practical'),
('CSDL701','Department Level Optional Course-3 Lab',1,7,4,1,'Practical'),
('CSDL702','Department Level Optional Course-4 Lab',1,7,4,1,'Practical'),
('CSP701','Major Project 1',1,7,4,3,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('CSC801','Distributed Computing',1,8,4,3,'Theory'),
('CSDC801','Department Level Optional Course-5',1,8,4,3,'Elective'),
('CSDC802','Department Level Optional Course-6',1,8,4,3,'Elective'),
('CILO801','Institute Level Optional Course-2',1,8,4,3,'Elective'),
('CSL801','Distributed Computing Lab',1,8,4,1,'Practical'),
('CSDL801','Department Level Optional Course-5 Lab',1,8,4,1,'Practical'),
('CSDL802','Department Level Optional Course-6 Lab',1,8,4,1,'Practical'),
('CSP801','Major Project 2',1,8,4,6,'Practical');

-- ================================================================
--  DEPT 2 — COMPUTER ENGINEERING AI, DS, ML (AIML)
-- ================================================================

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC101','Engineering Mathematics I',2,1,1,4,'Theory'),
('AIC102','Engineering Physics',2,1,1,4,'Theory'),
('AIC103','Engineering Chemistry',2,1,1,4,'Theory'),
('AIC104','Engineering Mechanics',2,1,1,4,'Theory'),
('AIC105','Basic Electrical & Electronics Engg',2,1,1,4,'Theory'),
('AIL101','Engineering Physics Lab',2,1,1,2,'Practical'),
('AIL102','Engineering Chemistry Lab',2,1,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC201','Engineering Mathematics II',2,2,1,4,'Theory'),
('AIC202','Programming & Problem Solving',2,2,1,4,'Theory'),
('AIC203','Engineering Drawing',2,2,1,4,'Theory'),
('AIC204','Environmental Studies',2,2,1,3,'Theory'),
('AIC205','Communication Skills',2,2,1,3,'Theory'),
('AIL201','Programming Lab',2,2,1,2,'Practical'),
('AIL202','Engineering Drawing Lab',2,2,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC301','Engineering Mathematics III',2,3,2,4,'Theory'),
('AIC302','Data Structures',2,3,2,4,'Theory'),
('AIC303','Digital Logic & Computer Organization',2,3,2,4,'Theory'),
('AIC304','Discrete Mathematics & Graph Theory',2,3,2,4,'Theory'),
('AIC305','Computer Graphics',2,3,2,4,'Theory'),
('AIL301','Data Structures Lab',2,3,2,2,'Practical'),
('AIL302','Computer Graphics Lab',2,3,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC401','Engineering Mathematics IV',2,4,2,4,'Theory'),
('AIC402','Analysis of Algorithms',2,4,2,4,'Theory'),
('AIC403','Database Management Systems',2,4,2,4,'Theory'),
('AIC404','Operating System',2,4,2,4,'Theory'),
('AIC405','Statistics for Machine Learning',2,4,2,4,'Theory'),
('AIL401','DBMS Lab',2,4,2,2,'Practical'),
('AIL402','Statistics Lab',2,4,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC501','Computer Network',2,5,3,3,'Theory'),
('AIC502','Web Computing',2,5,3,3,'Theory'),
('AIC503','Artificial Intelligence',2,5,3,3,'Theory'),
('AIC504','Data Warehousing & Mining',2,5,3,3,'Theory'),
('AIDLO5011','Statistics for Artificial Intelligence & Data Science',2,5,3,3,'Elective'),
('AIDLO5012','Advanced Algorithms',2,5,3,3,'Elective'),
('AIDLO5013','Internet of Things',2,5,3,3,'Elective'),
('AIL501','Web Computing and Network Lab',2,5,3,1,'Practical'),
('AIL502','Artificial Intelligence Lab',2,5,3,1,'Practical'),
('AIL503','Data Warehousing & Mining Lab',2,5,3,1,'Practical'),
('AIL504','Business Communication and Ethics-II',2,5,3,2,'Practical'),
('AIP501','Mini Project: 2A',2,5,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC601','Data Analytics and Visualization',2,6,3,3,'Theory'),
('AIC602','Cryptography and System Security',2,6,3,3,'Theory'),
('AIC603','Software Engineering and Project Management',2,6,3,3,'Theory'),
('AIC604','Machine Learning',2,6,3,3,'Theory'),
('AIDLO6012','Distributed Computing',2,6,3,3,'Elective'),
('AIL601','Data Analytics and Visualization Lab',2,6,3,1,'Practical'),
('AIL602','Cryptography & System Security Lab',2,6,3,1,'Practical'),
('AIL603','Software Engineering and Project Management Lab',2,6,3,1,'Practical'),
('AIL604','Machine Learning Lab',2,6,3,1,'Practical'),
('AIL605','Skill base Lab Course: Cloud Computing',2,6,3,2,'Practical'),
('AIP601','Mini Project Lab: 2B',2,6,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC701','Deep Learning',2,7,4,3,'Theory'),
('AIC702','Big Data Analytics',2,7,4,3,'Theory'),
('AIC703','Department Level Optional Course-3',2,7,4,3,'Elective'),
('AIC704','Department Level Optional Course-4',2,7,4,3,'Elective'),
('AIC705','Institute Level Optional Course-1',2,7,4,3,'Elective'),
('AIL701','Deep Learning Lab',2,7,4,1,'Practical'),
('AIL702','Big Data Analytics Lab',2,7,4,1,'Practical'),
('AIL703','Department Level Optional Course-3 Lab',2,7,4,1,'Practical'),
('AIL704','Department Level Optional Course-4 Lab',2,7,4,1,'Practical'),
('AIP701','Major Project 1',2,7,4,3,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('AIC801','Advanced Artificial Intelligence',2,8,4,3,'Theory'),
('AIC802','Department Level Optional Course-5',2,8,4,3,'Elective'),
('AIC803','Department Level Optional Course-6',2,8,4,3,'Elective'),
('AIC804','Institute Level Optional Course-2',2,8,4,3,'Elective'),
('AIL801','Advanced Artificial Intelligence Lab',2,8,4,1,'Practical'),
('AIL802','Department Level Optional Course-5 Lab',2,8,4,1,'Practical'),
('AIL803','Department Level Optional Course-6 Lab',2,8,4,1,'Practical'),
('AIP801','Major Project 2',2,8,4,6,'Practical');

-- ================================================================
--  DEPT 3 — INFORMATION TECHNOLOGY (DATA)
-- ================================================================

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC101','Engineering Mathematics I',3,1,1,4,'Theory'),
('ITC102','Engineering Physics',3,1,1,4,'Theory'),
('ITC103','Engineering Chemistry',3,1,1,4,'Theory'),
('ITC104','Engineering Mechanics',3,1,1,4,'Theory'),
('ITC105','Basic Electrical & Electronics Engg',3,1,1,4,'Theory'),
('ITL101','Engineering Physics Lab',3,1,1,2,'Practical'),
('ITL102','Engineering Chemistry Lab',3,1,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC201','Engineering Mathematics II',3,2,1,4,'Theory'),
('ITC202','Programming & Problem Solving',3,2,1,4,'Theory'),
('ITC203','Engineering Drawing',3,2,1,4,'Theory'),
('ITC204','Environmental Studies',3,2,1,3,'Theory'),
('ITC205','Communication Skills',3,2,1,3,'Theory'),
('ITL201','Programming Lab',3,2,1,2,'Practical'),
('ITL202','Engineering Drawing Lab',3,2,1,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC301','Engineering Mathematics III',3,3,2,4,'Theory'),
('ITC302','Data Structure & Algorithm',3,3,2,4,'Theory'),
('ITC303','Computer Organization',3,3,2,4,'Theory'),
('ITC304','Database Management Systems',3,3,2,4,'Theory'),
('ITC305','Discrete Mathematics',3,3,2,4,'Theory'),
('ITL301','DSA Lab',3,3,2,2,'Practical'),
('ITL302','DBMS Lab',3,3,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC401','Engineering Mathematics IV',3,4,2,4,'Theory'),
('ITC402','Analysis of Algorithms',3,4,2,4,'Theory'),
('ITC403','Operating System',3,4,2,4,'Theory'),
('ITC404','Computer Networks',3,4,2,4,'Theory'),
('ITC405','Object Oriented Analysis & Design',3,4,2,4,'Theory'),
('ITL401','OOP Lab',3,4,2,2,'Practical'),
('ITL402','OS Lab',3,4,2,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC501','Computer Network',3,5,3,3,'Theory'),
('ITC502','Web Computing',3,5,3,3,'Theory'),
('ITC503','Artificial Intelligence',3,5,3,3,'Theory'),
('ITC504','Data Warehousing & Mining',3,5,3,3,'Theory'),
('DTDLO5011','Statistics for Artificial Intelligence & Data Science',3,5,3,3,'Elective'),
('ITL501','Web Computing and Network Lab',3,5,3,1,'Practical'),
('ITL502','Artificial Intelligence Lab',3,5,3,1,'Practical'),
('ITL503','Data Warehousing & Mining Lab',3,5,3,1,'Practical'),
('ITP501','Mini Project: 2A',3,5,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('ITC601','Data Analytics and Visualization',3,6,3,3,'Theory'),
('ITC602','Cryptography and System Security',3,6,3,3,'Theory'),
('ITC603','Software Engineering and Project Management',3,6,3,3,'Theory'),
('ITC604','Machine Learning',3,6,3,3,'Theory'),
('DTDLO6012','Distributed Computing',3,6,3,3,'Elective'),
('ITL601','Data Analytics and Visualization Lab',3,6,3,1,'Practical'),
('ITL602','Cryptography & System Security Lab',3,6,3,1,'Practical'),
('ITL603','Software Engineering and Project Management Lab',3,6,3,1,'Practical'),
('ITL604','Machine Learning Lab',3,6,3,1,'Practical'),
('ITL605','Skill base Lab Course: Cloud Computing',3,6,3,2,'Practical'),
('ITP601','Mini Project Lab: 2B',3,6,3,2,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('DTC701','Deep Learning',3,7,4,3,'Theory'),
('DTC702','Big Data Analytics',3,7,4,3,'Theory'),
('DTC703','Department Level Optional Course-3',3,7,4,3,'Elective'),
('DTC704','Department Level Optional Course-4',3,7,4,3,'Elective'),
('DTC705','Institute Level Optional Course-1',3,7,4,3,'Elective'),
('DTL701','Deep Learning Lab',3,7,4,1,'Practical'),
('DTL702','Big Data Analytics Lab',3,7,4,1,'Practical'),
('DTL703','Department Level Optional Course-3 Lab',3,7,4,1,'Practical'),
('DTL704','Department Level Optional Course-4 Lab',3,7,4,1,'Practical'),
('DTP701','Major Project 1',3,7,4,3,'Practical');

INSERT INTO subjects (code,name,department_id,semester,year,credits,subject_type) VALUES
('DTC801','Advanced Artificial Intelligence',3,8,4,3,'Theory'),
('DTC802','Department Level Optional Course-5',3,8,4,3,'Elective'),
('DTC803','Department Level Optional Course-6',3,8,4,3,'Elective'),
('DTC804','Institute Level Optional Course-2',3,8,4,3,'Elective'),
('DTL801','Advanced Artificial Intelligence Lab',3,8,4,1,'Practical'),
('DTL802','Department Level Optional Course-5 Lab',3,8,4,1,'Practical'),
('DTL803','Department Level Optional Course-6 Lab',3,8,4,1,'Practical'),
('DTP801','Major Project 2',3,8,4,6,'Practical');

-- ================================================================
--  Assign demo teacher (sharma@college.edu) to COMP Sem 3 & 4
-- ================================================================
SET @tid = (SELECT t.id FROM teachers t JOIN users u ON u.id=t.user_id WHERE u.email='sharma@college.edu' LIMIT 1);
SET @ay  = (SELECT id FROM academic_years WHERE is_current=1 LIMIT 1);

INSERT IGNORE INTO teacher_subjects (teacher_id, subject_id, academic_year_id)
SELECT @tid, s.id, @ay
FROM subjects s
WHERE s.department_id = 1 AND s.semester IN (3, 4) AND @tid IS NOT NULL;

SELECT CONCAT('SUCCESS! Total subjects: ', COUNT(*)) AS result FROM subjects;
