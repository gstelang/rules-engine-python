import sqlite3

con = sqlite3.connect("rules_db.sqlite")
con.executescript("""
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE bad_values
(
    type  TEXT not null,
    value TEXT not null
);
INSERT INTO bad_values VALUES('subject','won lottery');
INSERT INTO bad_values VALUES('subject','don''t miss');
INSERT INTO bad_values VALUES('subject','dear friend');
INSERT INTO bad_values VALUES('body','send money');
INSERT INTO bad_values VALUES('body','once in a lifetime opportunity');
INSERT INTO bad_values VALUES('domain','hacker.com');
INSERT INTO bad_values VALUES('domain','bestopportunity.com');
COMMIT;
""")
