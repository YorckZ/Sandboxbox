import sqlite3

# Constants:
DB_PATH = "database/database.db"

# <editor-fold desc="Logic">
"""
CRUD:
======
x Create
x Read
x Update
x Delete
======

x initialize_db()
x open_connection()
x close_connection()
x get_next_id()

x create_element()
x delete_element()

x create_question()
x read_question()
x update_question()
x delete_question()

x create_answer()
x read_answer()
x update_answer()
x delete_answer()

x create_prompt()
x read_prompt()
x update_prompt()
x delete_prompt()
"""
# </editor-fold>

# <editor-fold desc="Fundamental Database Functions">
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

    conn, cursor = open_connection()

    # tbl_elemente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_elemente (
        ID INTEGER NOT NULL PRIMARY KEY , -- Primary Key
        table_id INTEGER NOT NULL, -- 1=Frage, 2=Antwort, 3=Prompt
        foreign_id INTEGER NOT NULL
        )
    """)

    # tbl_fragen
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_fragen (
                ID INTEGER NOT NULL PRIMARY KEY, -- Primary Key
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
                ID INTEGER NOT NULL PRIMARY KEY, -- Primary Key
                Bez TEXT NOT NULL,  -- Kurzbezeichnung der Antworten
                Text TEXT NOT NULL) -- Text der Antwort
            """)

    # tbl_prompts
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_prompts (
                ID INTEGER NOT NULL PRIMARY KEY, -- Primary Key
                Bez TEXT NOT NULL, -- Kurzbezeichnung der Prompt
                System TEXT NOT NULL, -- Text des Prompts
                DSGVO TEXT, -- Text der DSGVO
                Task TEXT -- Aufgabe des LLMs
                )
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
# </editor-fold>

# ===========================================================================================================

def create_element(table_id: int, element_id: int):
    try:
        conn, cursor = open_connection()
        e_id = get_next_id()
        cursor.execute("INSERT INTO tbl_elemente (ID, table_id, foreign_id) VALUES (?, ?, ?);", (e_id, table_id, element_id))
        conn.commit()
        close_connection(conn)
        print("Element inserted successfully. New ID:", cursor.lastrowid)
    except Exception as e:
        print("Error inserting data:", e)

def delete_element(e_id):
    conn, cursor = open_connection()
    cursor.execute("DELETE FROM tbl_elemente WHERE foreign_id = ?", (e_id,))
    conn.commit()
    close_connection(conn)

# ===========================================================================================================

def create_frage(bez: str, text: str, bem: str, ja: int, nein: int, unsicher: int, initial: bool):
    conn = None

    try:
        conn, cursor = open_connection()
        element_id: int = get_next_id()
        create_element(1, element_id)

        cursor.execute("INSERT INTO tbl_fragen (ID, Bez, Text, Bem, Ja, Nein, unsicher, Initial) VALUES ("
                       "?, ?, ?, ?, ?, ?, ?, ?);", (element_id, bez, text, bem, ja, nein, unsicher, initial))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def get_all_fragen():
    """Fetches all questions' IDs and names from tbl_fragen."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez FROM tbl_fragen")
    fragen = cursor.fetchall()
    close_connection(conn)
    return [{"ID": row[0], "Bez": row[1]} for row in fragen]

def get_frage_by_id(frage_id: int):
    """Fetches a single frage by ID."""
    conn, cursor = open_connection()
    cursor.execute("SELECT Bez, Text, Bem, Ja, Nein, unsicher, Initial FROM tbl_fragen WHERE ID = ?", (frage_id,))
    frage = cursor.fetchone()
    close_connection(conn)

    if frage:
        return {"Bez": frage[0], "Text": frage[1], "Bem": frage[2], "Ja": frage[3], "Nein": frage[4], "unsicher": frage[5], "Initial": frage[6]}
    return None

def update_frage(frage_id: int, bez: str, text: str, bem: str, ja: int, nein: int, unsicher: int, initial: bool):
    """Updates an existing frage."""
    conn, cursor = open_connection()
    cursor.execute("""
        UPDATE tbl_fragen SET Bez = ?, Text = ?, Bem = ?, Ja = ?, Nein = ?, unsicher = ?, Initial = ? WHERE ID = ?
    """, (bez, text, bem, ja, nein, unsicher, initial, frage_id))
    conn.commit()
    close_connection(conn)

def delete_frage(frage_id: int):
    """Deletes a prompt from tbl_prompts based on the given ID."""
    conn, cursor = open_connection()
    delete_element(frage_id)
    cursor.execute("DELETE FROM tbl_fragen WHERE ID = ?", (frage_id,))
    conn.commit()
    close_connection(conn)

# ===========================================================================================================

def create_antwort(bez: str, text: str):
    conn = None

    try:
        conn, cursor = open_connection()
        element_id: int = get_next_id()
        create_element(2, element_id)

        cursor.execute("INSERT INTO tbl_antworten (ID, Bez, Text) VALUES (?, ?, ?);", (element_id, bez, text))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def get_all_antworten():
    """Fetches all antwort IDs and names from tbl_antworten."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez, Text FROM tbl_antworten")
    antworten = cursor.fetchall()
    close_connection(conn)
    return [{"ID": row[0], "Bez": row[1], "Text": row[2]} for row in antworten]

def get_antwort_by_id(antwort_id: int):
    """Fetches a single antwort by ID."""
    conn, cursor = open_connection()
    cursor.execute("SELECT Bez, Text FROM tbl_antworten WHERE ID = ?", (antwort_id,))
    antwort = cursor.fetchone()
    close_connection(conn)

    if antwort:
        return {"Bez": antwort[0], "Text": antwort[1]}
    return None

def update_antwort(antwort_id: int, bez: str, text: str):
    """Updates an existing antwort."""
    conn, cursor = open_connection()
    cursor.execute("""
        UPDATE tbl_antworten SET Bez = ?, Text = ? WHERE ID = ?
    """, (bez, text, antwort_id))
    conn.commit()
    close_connection(conn)

def delete_antwort(antwort_id: int):
    """Deletes an antwort from tbl_antworten based on the given ID."""
    conn, cursor = open_connection()
    delete_element(antwort_id)
    cursor.execute("DELETE FROM tbl_antworten WHERE ID = ?", (antwort_id,))
    conn.commit()
    close_connection(conn)

# ===========================================================================================================

def create_prompt(bez:str, system: str, dsgvo: str, task: str):
    conn = None

    try:
        conn, cursor = open_connection()
        element_id: int = get_next_id()
        create_element(3, element_id)

        cursor.execute("INSERT INTO tbl_prompts (ID, Bez, System, DSGVO, Task) VALUES (?, ?, ?, ?, ?);", (element_id, bez, system, dsgvo, task))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def get_all_prompts():
    """Fetches all prompts' IDs and names from tbl_prompts."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez FROM tbl_prompts")
    prompts = cursor.fetchall()
    close_connection(conn)
    return [{"ID": row[0], "Bez": row[1]} for row in prompts]

def get_prompt_by_id(prompt_id):
    """Fetches a single prompt by ID."""
    conn, cursor = open_connection()
    cursor.execute("SELECT Bez, System, DSGVO, Task FROM tbl_prompts WHERE ID = ?", (prompt_id,))
    prompt = cursor.fetchone()
    close_connection(conn)

    if prompt:
        return {"Bez": prompt[0], "System": prompt[1], "DSGVO": prompt[2], "Task": prompt[3]}
    return None

def update_prompt(prompt_id, bez, system, dsgvo, task):
    """Updates an existing prompt."""
    conn, cursor = open_connection()
    cursor.execute("""
        UPDATE tbl_prompts SET Bez = ?, System = ?, DSGVO = ?, Task = ? WHERE ID = ?
    """, (bez, system, dsgvo, task, prompt_id))
    conn.commit()
    close_connection(conn)

def delete_prompt(prompt_id):
    """Deletes a prompt from tbl_prompts based on the given ID."""
    conn, cursor = open_connection()
    delete_element(prompt_id)
    cursor.execute("DELETE FROM tbl_prompts WHERE ID = ?", (prompt_id,))
    conn.commit()
    close_connection(conn)

# ===========================================================================================================

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

def admin_nuke_database():
    admin_clean_all()
    init_db()

# ===========================================================================================================

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

def admin_print_all_tables():
    admin_print_tbl_elemente()
    admin_print_tbl_fragen()
    admin_print_tbl_antworten()
    admin_print_tbl_prompts()

# ===========================================================================================================


if __name__ == '__main__':
    DB_PATH = "database.db"
    # admin_nuke_database()
    # admin_clean_all()
    init_db()
    # admin_print_all_tables()
    #
    # insert_into_tbl_fragen("Frage1", "Frage1", "Frage1", 1, 2, 3, False)
    # insert_into_tbl_antworten("Antwort1")
    # insert_into_tbl_prompts("Prompt1")
    #
    # admin_print_tbl_fragen()
    # admin_print_tbl_antworten()
    # admin_print_tbl_prompts()
    # admin_print_tbl_elemente()
    #
    # admin_clean_fragen()
    # admin_clean_antworten()
    # admin_clean_prompts()

    # admin_print_tbl_fragen()
    # admin_print_tbl_antworten()
    # admin_print_tbl_prompts()
    # admin_print_tbl_elemente()
