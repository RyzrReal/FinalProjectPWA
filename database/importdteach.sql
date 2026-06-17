DROP TABLE IF EXISTS importdteach;

CREATE TABLE importdteach (
    Teachid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    faculty TEXT NOT NULL,
    course_taught TEXT,
    carcolour TEXT,
    priority INTEGER DEFAULT 1
);