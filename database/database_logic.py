import sqlite3

# Constants:
DB_PATH = "database/database.db"

# <editor-fold desc="Logic">
"""
(S)CRUD:
======
Search
x Create
Read
Update
Delete




get_max_element_ID()
create_element()

create_question()
    open_connection()
	get_max_element_ID()
	create_element()
	close_connection()
create_answer()
	...
create_prompt()
	...

update_question()
update_answer()
update_prompt()

delete_question_from_elements()
delete_answer_from_elements()
delete_prompt_from_elements()

delete_question()
	delete_question_from_elements()
delete_answer()
	delete_answer_from_elements()
delete_prompt()
	delete_prompt_from_elements()
"""
# </editor-fold>

def open_connection():
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        return connection, cursor
    except Exception as e:
        print(e)

def close_connection(connection: sqlite3.Connection):
    try:
        connection.close()
    except Exception as e:
        print(e)

def init_db():
    # with sqlite3.connect(DB_PATH) as conn:
        # cursor = conn.cursor()

    conn, cursor = open_connection()

    # tbl_elemente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_elemente (
        ID INTEGER NOT NULL, -- Primary Key
        TYP INTEGER NOT NULL -- 1=Frage, 2=Antwort, 3=Prompt
        )
    """)

    # tbl_fragen
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_fragen (
                ID INTEGER NOT NULL, -- Primary Key
                Bez Text NOT NULL, -- Kurzbezeichnung der Frage
                Text TEXT NOT NULL, -- Fragetext
                Bem Text, -- Ergänzungstext, Hilfetext
                Ja INTEGER, -- Verknüpfung zu nächsten Element; Foreign Key
                Nein INTEGER, -- Verknüpfung zu nächsten Element; Foreign Key
                unsicher INTEGER, -- Verknüpfung zu nächsten Element; Foreign Key
                Initial BOOLEAN -- Ist dies die Startfrage
                )
            """)

    # tbl_antworten
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_antworten (
                ID INTEGER NOT NULL, -- Primary Key
                Text TEXT NOT NULL) -- Text der Antwort
            """)

    # tbl_prompts
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_prompts (
                ID INTEGER NOT NULL , -- Primary Key
                Text TEXT NOT NULL) -- Text des Prompts
            """)

    conn.commit()
    close_connection(conn)

def get_next_id() -> int:
    try:
        conn, cursor = open_connection()
        cursor.execute("SELECT MAX(ID) FROM tbl_elemente;")
        highest_id = cursor.fetchone()[0]

        if highest_id is None:
            highest_id = 0

        close_connection(conn)
        return highest_id + 1
    except Exception as e:
        print(e)
        return -1

def insert_into_tbl_elemente(element: int, typ: int):
    try:
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()
        conn, cursor = open_connection()
        cursor.execute("INSERT INTO tbl_elemente (ID, TYP) VALUES (?, ?);", (element, typ))
        conn.commit()
        close_connection(conn)
        print("Element inserted successfully. New ID:", cursor.lastrowid)
    except Exception as e:
        print("Error inserting data:", e)

def insert_into_tbl_prompts(text: str):
    conn = None

    try:
        conn, cursor = open_connection()
        element: int = get_next_id()
        insert_into_tbl_elemente(element, 3)

        cursor.execute("INSERT INTO tbl_prompts (ID, Text) VALUES (?, ?);", (element, text))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def insert_into_tbl_antworten(text: str):
    conn = None

    try:
        conn, cursor = open_connection()
        element: int = get_next_id()
        insert_into_tbl_elemente(element, 2)

        cursor.execute("INSERT INTO tbl_antworten (ID, Text) VALUES (?, ?);", (element, text))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def insert_into_tbl_fragen(bez: str, text: str, bem: str, ja: int, nein: int, unsicher: int, initial: bool):
    conn = None

    try:
        conn, cursor = open_connection()
        element: int = get_next_id()
        insert_into_tbl_elemente(element, 1)

        cursor.execute("INSERT INTO tbl_fragen (ID, Bez, Text, Bem, Ja, Nein, unsicher, Initial) VALUES ("
                       "?, ?, ?, ?, ?, ?, ?, ?);", (element, bez, text, bem, ja, nein, unsicher, initial))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def admin_clear_all_tables():
    """
    Deletes all rows from all tables in the SQLite3 database but keeps the empty tables.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        # Iterate through each table and delete its contents
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE * FROM {table_name};")
            cursor.execute(f"VACUUM;")  # Optional: Reclaim free space

        conn.commit()
        conn.close()
        print("All table entries deleted successfully.")
    except Exception as e:
        print(f"Error: {e}")

def admin_clean_fragen():
    try:
        conn, cursor = open_connection()

        # Check if tbl_fragen has any entries
        cursor.execute("SELECT COUNT(*) FROM tbl_fragen")
        count = cursor.fetchone()[0]

        if count > 0:
            # Delete from tbl_elemente where ID matches tbl_fragen
            cursor.execute("""
                DELETE FROM tbl_elemente
                WHERE ID IN (SELECT ID FROM tbl_fragen)
            """
            )

            # Delete all entries from tbl_fragen
            cursor.execute("DELETE FROM tbl_fragen WHERE ID IS NOT NULL")

        conn.commit()
        close_connection(conn)
        print("All fragen entries deleted successfully.")
    except Exception as e:
        print(e)

def admin_clean_antworten():
    try:
        conn, cursor = open_connection()

        # Check if tbl_antworten has any entries
        cursor.execute("SELECT COUNT(*) FROM tbl_antworten")
        count = cursor.fetchone()[0]

        if count > 0:
            # Delete from tbl_elemente where ID matches tbl_antworten
            cursor.execute("""
                DELETE FROM tbl_elemente
                WHERE ID IN (SELECT ID FROM tbl_antworten)
            """
            )

            # Delete all entries from tbl_antworten
            cursor.execute("DELETE FROM tbl_antworten WHERE ID IS NOT NULL")

        conn.commit()
        close_connection(conn)
        print("All antworten entries deleted successfully.")
    except Exception as e:
        print(e)

def admin_clean_prompts():
    try:
        conn, cursor = open_connection()

        # Check if tbl_prompts has any entries
        cursor.execute("SELECT COUNT(*) FROM tbl_prompts")
        count = cursor.fetchone()[0]

        if count > 0:
            # Delete from tbl_elemente where ID matches tbl_prompts
            cursor.execute("""
                DELETE FROM tbl_elemente
                WHERE ID IN (SELECT ID FROM tbl_prompts)
            """
            )

            # Delete all entries from tbl_prompts
            cursor.execute("DELETE FROM tbl_prompts WHERE ID IS NOT NULL")

        conn.commit()
        close_connection(conn)
        print("All prompts entries deleted successfully.")
    except Exception as e:
        print(e)

def admin_clean_all():
    try:
        conn, cursor = open_connection()
        # cursor.execute("DELETE FROM tbl_prompts;")
        # cursor.execute("DELETE FROM tbl_antworten;")
        # cursor.execute("DELETE FROM tbl_fragen;")
        # cursor.execute("DELETE FROM tbl_elemente;")
        cursor.execute("DELETE FROM tbl_prompts WHERE ID IS NOT NULL;")
        cursor.execute("DELETE FROM tbl_antworten WHERE ID IS NOT NULL;")
        cursor.execute("DELETE FROM tbl_fragen WHERE ID IS NOT NULL;")
        cursor.execute("DELETE FROM tbl_elemente WHERE ID IS NOT NULL;")
        conn.commit()
        conn.close()
        print("All database entries deleted successfully.")
    except Exception as e:
        print(e)

def admin_print_tbl_fragen():
    try:
        conn, cursor = open_connection()

        # Retrieve all rows from tbl_fragen
        cursor.execute("SELECT * FROM tbl_fragen")
        rows = cursor.fetchall()
        conn.commit()
        close_connection(conn)

        # Print each row
        for row in rows:
            print(row)

        print("All fragen displayed successfully.")
    except Exception as e:
        print(e)

def admin_print_tbl_antworten():
    try:
        conn, cursor = open_connection()

        # Retrieve all rows from tbl_antworten
        cursor.execute("SELECT * FROM tbl_antworten")
        rows = cursor.fetchall()
        conn.commit()
        close_connection(conn)

        # Print each row
        for row in rows:
            print(row)

        print("All antworten displayed successfully.")
    except Exception as e:
        print(e)

def admin_print_tbl_prompts():
    try:
        conn, cursor = open_connection()

        # Retrieve all rows from tbl_prompts
        cursor.execute("SELECT * FROM tbl_prompts")
        rows = cursor.fetchall()
        conn.commit()
        close_connection(conn)

        # Print each row
        for row in rows:
            print(row)

        print("All prompts displayed successfully.")
    except Exception as e:
        print(e)

def admin_print_tbl_elemente():
    try:
        conn, cursor = open_connection()

        # Retrieve all rows from tbl_elemente
        cursor.execute("SELECT * FROM tbl_elemente")
        rows = cursor.fetchall()
        conn.commit()
        close_connection(conn)

        # Print each row
        for row in rows:
            print(row)

        print("All elemente displayed successfully.")
    except Exception as e:
        print(e)


if __name__ == '__main__':
    init_db()
    admin_clean_all()

    insert_into_tbl_fragen("Frage1", "Frage1", "Frage1", 1, 2, 3, False)
    insert_into_tbl_antworten("Antwort1")
    insert_into_tbl_prompts("Prompt1")

    admin_print_tbl_fragen()
    admin_print_tbl_antworten()
    admin_print_tbl_prompts()
    admin_print_tbl_elemente()

    admin_clean_fragen()
    admin_clean_antworten()
    admin_clean_prompts()

    admin_print_tbl_fragen()
    admin_print_tbl_antworten()
    admin_print_tbl_prompts()
    admin_print_tbl_elemente()

