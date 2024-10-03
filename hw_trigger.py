"""

--------------------------------- Create tables

-- Students table with course_avg_grades and num_courses dynamically updated
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    course_avg_grades REAL DEFAULT 0,  -- Will be dynamically updated with triggers
    num_courses INT DEFAULT 0          -- Will be dynamically updated with triggers
);

-- Courses table with total_num_of_students dynamically updated
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100),
    total_num_of_students INT DEFAULT 0  -- Will be dynamically updated with triggers
);

-- Grades table with a composite primary key of student_id and course_id
CREATE TABLE grades (
    student_id INT,
    course_id INT,
    grade REAL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Insert 30 students
INSERT INTO students (name, email) VALUES
('Alice', 'alice@example.com'),
('Bob', 'bob@example.com'),
('Charlie', 'charlie@example.com'),
('David', 'david@example.com'),
('Eve', 'eve@example.com'),
('Frank', 'frank@example.com'),
('Grace', 'grace@example.com'),
('Hank', 'hank@example.com'),
('Ivy', 'ivy@example.com'),
('Jack', 'jack@example.com'),
('Kevin', 'kevin@example.com'),
('Laura', 'laura@example.com'),
('Michael', 'michael@example.com'),
('Nancy', 'nancy@example.com'),
('Oscar', 'oscar@example.com'),
('Pam', 'pam@example.com'),
('Quinn', 'quinn@example.com'),
('Rick', 'rick@example.com'),
('Steve', 'steve@example.com'),
('Tina', 'tina@example.com'),
('Uma', 'uma@example.com'),
('Victor', 'victor@example.com'),
('Wendy', 'wendy@example.com'),
('Xander', 'xander@example.com'),
('Yvonne', 'yvonne@example.com'),
('Zach', 'zach@example.com'),
('Amber', 'amber@example.com'),
('Bruce', 'bruce@example.com'),
('Clara', 'clara@example.com');

-- Insert 8 courses
INSERT INTO courses (course_name) VALUES
('Mathematics'),
('Physics'),
('Chemistry'),
('Biology'),
('History'),
('Geography'),
('Literature'),
('Computer Science');

--------------------------------- Create random grades

WITH random_grades AS (
    SELECT
        s.student_id,
        (random() * 8 + 1)::int as course_id,  -- Ensures course_id is between 1 and 8
        (random() * (100-55+1) + 55)::int as grade  -- Generates integer grades between 55 and 100
    FROM
        generate_series(1, 29) s(student_id),  -- Student IDs from 1 to 29
        generate_series(1, (random() * (8-3) + 3)::int) g(num_grades) -- Generates between 3 and 8 grades
)
INSERT INTO grades (student_id, course_id, grade)
SELECT DISTINCT ON (student_id, course_id) student_id, course_id, grade
FROM random_grades
WHERE course_id BETWEEN 1 AND 8
ORDER BY student_id, course_id, grade;

--------------------------------- update avg and num_courses in students

UPDATE students s
SET
    course_avg_grades = (
        SELECT ROUND(AVG(grade)::numeric, 2)
        FROM grades g
        WHERE g.student_id = s.student_id
    ),
    num_courses = (
        SELECT COUNT(course_id)
        FROM grades g
        WHERE g.student_id = s.student_id
    )
where student_id >= 1 ;


--------------------------------- update total numbers of student for each course
UPDATE courses
SET total_num_of_students = COALESCE((
    SELECT COUNT(DISTINCT student_id)
    FROM grades
    WHERE grades.course_id = courses.course_id
), 0)
where course_id >= 1;
----------------------------------------------------------------------------
----------------------------------------------------------------------------

-- מה עושה פונקציה COALESCE ?

-- הפונקציה COALESCE משמשת בשפת SQL (וגם בשפות אחרות)
-- כדי להחזיר את הערך הראשון שאינו NULL מתוך רשימה של ערכים.
-- אם כל הערכים ברשימה הם NULL, היא מחזירה NULL.

-- בקטע הקוד הזה, הפונקציה COALESCE משמשת כדי
-- להבטיח שהערך המוגדר עבור total_num_of_students לא יהיה NULL.

SELECT COUNT(DISTINCT student_id)
FROM grades
WHERE grades.course_id = courses.course_id
-- תת-השאילתה מחשבת את מספר הסטודנטים הייחודיים הרשומים לכל קורס.
-- אם אין סטודנטים רשומים לקורס (ולכן השאילתה מחזירה NULL), נשתמש ב-COALESCE.

COALESCE((...), 0)
-- אם תת-השאילתה מחזירה NULL (כלומר, אין סטודנטים בקורס), הפונקציה COALESCE מחזירה 0.
-- כך, הערך המוקצה ל-total_num_of_students יהיה תמיד מספר (0 במקרה שאין תלמידים).
----------------------------------------------------------------------------------
----------------------------------------------------------------------------------

-- כעת הוסף triggers כך ש: כאשר נוסיף ציון של תלמיד ב טבלת ציונים, מספר התלמידים שלמדו
-- בקורס יתעדכן בהתאם )שים לב מספר התלמידים בקורס נקבע לפי ספירה של כמות הציונים( .
-- ועכשיו הוסף טריגר שכאשר נמחק ציון של תלמיד בטבלת ציונים , מספר התלמידים שלמדו בקורס
-- יתעדכן בהתאם

-- הוספת שני טריגרים: אחד עבור הוספת ציון ואחד עבור מחיקת ציון:
-- טריגר להוספת ציון

CREATE OR REPLACE FUNCTION update_student_count_on_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE courses
    SET total_num_of_students = (
        SELECT COUNT(DISTINCT student_id)
        FROM grades
        WHERE course_id = NEW.course_id
    )
    WHERE course_id = NEW.course_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_grade_insert
AFTER INSERT ON grades
FOR EACH ROW
EXECUTE FUNCTION update_student_count_on_insert();


-- טריגר למחיקת ציון

CREATE OR REPLACE FUNCTION update_student_count_on_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE courses
    SET total_num_of_students = (
        SELECT COUNT(DISTINCT student_id)
        FROM grades
        WHERE course_id = OLD.course_id
    )
    WHERE course_id = OLD.course_id;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_grade_delete
AFTER DELETE ON grades
FOR EACH ROW
EXECUTE FUNCTION update_student_count_on_delete();
----------------------------------------------------

-- כעת הוסף תלמיד ובדוק אם אכן מספר התלמידים בקורס השתנה בהתאם
-- לא לשכוח להגיש את פונקציית ה triggerואת הפונקציה שהיא מפעילה...

-- פונקציות הטריגר
-- פונקציה להוספת ציון (כפי שניתן קודם)

CREATE OR REPLACE FUNCTION update_student_count_on_insert()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE courses
    SET total_num_of_students = (
        SELECT COUNT(DISTINCT student_id)
        FROM grades
        WHERE course_id = NEW.course_id
    )
    WHERE course_id = NEW.course_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
----------------------

-- פונקציה למחיקת ציון (כפי שניתן קודם)

CREATE OR REPLACE FUNCTION update_student_count_on_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE courses
    SET total_num_of_students = (
        SELECT COUNT(DISTINCT student_id)
        FROM grades
        WHERE course_id = OLD.course_id
    )
    WHERE course_id = OLD.course_id;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
----------------------

-- יצירת הטריגרים
-- טריגר להוספת ציון

CREATE TRIGGER after_grade_insert
AFTER INSERT ON grades
FOR EACH ROW
EXECUTE FUNCTION update_student_count_on_insert();

-- טריגר למחיקת ציון
CREATE TRIGGER after_grade_delete
AFTER DELETE ON grades
FOR EACH ROW
EXECUTE FUNCTION update_student_count_on_delete();

-- הוספת תלמיד חדש וציון
-- נניח שנוסיף תלמיד חדש עם ציון בקורס מסוים:

-- הוספת תלמיד חדש
INSERT INTO students (name, email) VALUES ('John Doe', 'john@example.com');

-- נניח שהתלמיד קיבל ציון בקורס מספר 1
INSERT INTO grades (student_id, course_id, grade) VALUES (currval('students_student_id_seq'), 1, 85);

-- בדיקה של מספר התלמידים בקורס
-- כדי לבדוק אם מספר התלמידים בקורס השתנה, נוכל להריץ שאילתא על טבלת הקורסים:

SELECT course_id, total_num_of_students
FROM courses;
---------------------------------------------------------
---------------------------------------------------------

-- 2.
-- יצירת View להצגת כל הציונים עם שמות התלמידים ושמות הקורסים

CREATE VIEW all_grades AS
SELECT
    s.name AS student_name,
    c.course_name,
    g.grade
FROM
    grades g
JOIN
    students s ON g.student_id = s.student_id
JOIN
    courses c ON g.course_id = c.course_id;

-------------------------------------------------
--  הצג כדי להציג את כל הציונים מעל 80

CREATE VIEW high_grades AS
SELECT
    s.name AS student_name,
    c.course_name,
    g.grade
FROM
    grades g
JOIN
    students s ON g.student_id = s.student_id
JOIN
    courses c ON g.course_id = c.course_id
WHERE
    g.grade > 80;
-----------------------------------------------------
-- הצג כדי להציג את פרטי הקורס עם המספר הגבוה ביותר של תלמידים

CREATE VIEW course_with_most_students AS
SELECT
    c.course_name,
    c.total_num_of_students
FROM
    courses c
ORDER BY
    c.total_num_of_students DESC
LIMIT 1;
-----------------------------------------------------------
-- להצגת כל הציונים ביחד עם שמות התלמידים ושמות הקורסים
SELECT * FROM all_grades;

-- להצגת כל הציונים מעל 80
SELECT * FROM high_grades;

-- להצגת פרטי הקורס עם מספר התלמידים הגדול ביותר
SELECT * FROM course_with_most_students;
---------------------------------------------------------------
---------------------------------------------------------------
---------------------------------------------------------------
-- 3.
-- צור פונקציית procedure_stored אשר מחזירה את התלמיד עם הציון הגבוה ביותר
--  השאילתא ליצירת ה - procedure_stored + קוד של ההפעלה שלה

CREATE OR REPLACE FUNCTION procedure_stored()
RETURNS TABLE(student_name VARCHAR, course_name VARCHAR, grade REAL) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.name AS student_name,
        c.course_name,
        g.grade
    FROM
        grades g
    JOIN
        students s ON g.student_id = s.student_id
    JOIN
        courses c ON g.course_id = c.course_id
    ORDER BY
        g.grade DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
----------------------

-- הפעלת הפונקציה כדי לקבל את התלמיד עם הציון הגבוה ביותר
SELECT * FROM procedure_stored();

"""