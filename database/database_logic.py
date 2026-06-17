import sqlite3
import json

# Constants:
DB_PATH = "database/database.db"

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
                Unsicher INTEGER, -- Verknüpfung zu nächsten Element; Foreign Key
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
    # cursor.execute("""
    #             CREATE TABLE IF NOT EXISTS tbl_prompts (
    #             ID INTEGER NOT NULL PRIMARY KEY, -- Primary Key
    #             Bez TEXT NOT NULL, -- Kurzbezeichnung der Prompt
    #             System TEXT NOT NULL, -- Text des Prompts
    #             DSGVO TEXT, -- Text der DSGVO
    #             Task TEXT -- Aufgabe des LLMs
    #             )
    #         """)

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_prompts (
                ID INTEGER NOT NULL PRIMARY KEY, -- Primary Key
                Bez TEXT NOT NULL, -- Kurzbezeichnung des Prompts
                Frage TEXT, -- Referenz/Frage (String)
                DSGVO TEXT -- DSGVO-Artikel (Wortlaut)
                )
            """)

    # tbl_config (global configuration – single row expected)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_config (
            ID INTEGER NOT NULL PRIMARY KEY,
            email_recipient TEXT,
            email_subject TEXT,
            email_body TEXT
        )
    """)

    # tbl_llm_config (global LLM configuration – single row expected)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_llm_config (
            ID INTEGER NOT NULL PRIMARY KEY,
            provider TEXT NOT NULL DEFAULT 'ollama',

            ollama_base_url TEXT DEFAULT 'http://localhost:11434',
            ollama_model TEXT DEFAULT 'llama3.1',

            openai_api_key TEXT,
            openai_model TEXT DEFAULT 'gpt-4.1-mini',
            openai_base_url TEXT,

            temperature REAL DEFAULT 0.2,
            max_output_tokens INTEGER DEFAULT 1000
        )
    """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tbl_contact_requests(
                       ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                       organisation_name TEXT NOT NULL,
                       organisation_location TEXT,
                       contact_person TEXT NOT NULL,
                       phone_extension TEXT,
                       email TEXT NOT NULL,

                       product_description TEXT,
                       product_purpose TEXT,
                       development_stage TEXT,
                       data_categories_processing_output TEXT,
                       specific_questions_problems TEXT,
                       participation_timeline TEXT
                        )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tbl_contact_notification_config (
                       ID INTEGER NOT NULL PRIMARY KEY,
                       recipient TEXT NOT NULL,
                       subject TEXT NOT NULL,
                       body TEXT
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tbl_contact_company_email_config (
                       ID INTEGER NOT NULL PRIMARY KEY,
                       subject TEXT NOT NULL,
                       body TEXT
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tbl_smtp_config (
                       ID INTEGER NOT NULL PRIMARY KEY,
                       smtp_host TEXT NOT NULL,
                       smtp_port INTEGER NOT NULL DEFAULT 587,
                       smtp_user TEXT NOT NULL,
                       smtp_password TEXT NOT NULL,
                       smtp_from TEXT NOT NULL,
                       use_tls BOOLEAN NOT NULL DEFAULT 1
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

def get_element_by_id(element_id: int):
    """
    Looks up the element by its ID and returns a unified dict with its type and content.
    """
    conn, cursor = open_connection()
    cursor.execute("SELECT table_id, foreign_id FROM tbl_elemente WHERE ID = ?", (element_id,))
    row = cursor.fetchone()
    close_connection(conn)
    if not row:
        return None

    table_id, foreign_id = row

    if table_id == 1:  # Frage
        frage = get_frage_by_id(foreign_id)
        if frage:
            return {
                "type": "Frage",
                "ID": element_id,
                "FrageID": foreign_id,
                "Bez": frage["Bez"],
                "Text": frage["Text"],
                "Bem": frage["Bem"],
                "Ja": frage["Ja"],
                "Nein": frage["Nein"],
                "Unsicher": frage["Unsicher"],
                "Initial": frage["Initial"],
            }
    elif table_id == 2:  # Antwort
        antwort = get_antwort_by_id(foreign_id)
        if antwort:
            return {
                "type": "Antwort",
                "ID": element_id,
                "AntwortID": foreign_id,
                "Bez": antwort["Bez"],
                "Text": antwort["Text"],
            }
    # elif table_id == 3:  # Prompt
    #     prompt = get_prompt_by_id(foreign_id)
    #     if prompt:
    #         return {
    #             "type": "Prompt",
    #             "ID": element_id,
    #             "PromptID": foreign_id,
    #             "Bez": prompt["Bez"],
    #             "System": prompt["System"],
    #             "DSGVO": prompt.get("DSGVO", ""),
    #             "Task": prompt.get("Task", ""),
    #         }

    # TODO: Simplify
    elif table_id == 3:  # Prompt
        prompt = get_prompt_by_id(foreign_id)
        if prompt:
            # Include a 'System' field for backward-compatibility with the frontend display
            system_text = ""
            if prompt.get("Frage"):
                system_text += str(prompt["Frage"]).strip()
            if prompt.get("DSGVO"):
                if system_text:
                    system_text += "\n\n"
                system_text += str(prompt["DSGVO"]).strip()

            return {
                "type": "Prompt",
                "ID": element_id,
                "PromptID": foreign_id,
                "Bez": prompt["Bez"],
                "Frage": prompt.get("Frage", ""),
                "DSGVO": prompt.get("DSGVO", ""),
                "System": system_text,  # for current new.html which reads element.System
            }

    return None

def get_all_bez_with_element_ids():
    """
    Return all elements as {ID=<tbl_elemente.ID>, Bez, type} sorted by Bez.
    """
    conn, cursor = open_connection()
    cursor.execute("""
        SELECT * FROM (
            SELECT e.ID AS ElementID, 'Frage' AS type, f.Bez AS Bez
            FROM tbl_elemente e
            JOIN tbl_fragen f ON f.ID = e.foreign_id
            WHERE e.table_id = 1
            UNION ALL
            SELECT e.ID AS ElementID, 'Antwort' AS type, a.Bez AS Bez
            FROM tbl_elemente e
            JOIN tbl_antworten a ON a.ID = e.foreign_id
            WHERE e.table_id = 2
            UNION ALL
            SELECT e.ID AS ElementID, 'Prompt' AS type, p.Bez AS Bez
            FROM tbl_elemente e
            JOIN tbl_prompts p ON p.ID = e.foreign_id
            WHERE e.table_id = 3
        ) t
        ORDER BY t.Bez COLLATE NOCASE ASC
    """)
    rows = cursor.fetchall()
    close_connection(conn)
    # rows: (ElementID, type, Bez)
    return [{"ID": r[0], "type": r[1], "Bez": r[2]} for r in rows]

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

def save_all_tables_to_json(json_path="database_export.json"):
    """
    Saves all rows from all tables into a single JSON file.
    The JSON file will be a dict where each key is the table name and the value is a list of dicts (rows).
    """
    try:
        conn, cursor = open_connection()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        export_data = {}

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            export_data[table] = [
                dict(zip(columns, row)) for row in rows
            ]

        with open(json_path, "w", encoding="utf-8") as f:
            json_str = json.dumps(export_data, ensure_ascii=False, indent=4)
            f.write(json_str)

        close_connection(conn)
        print(f"All tables have been exported to {json_path}")
    except Exception as e:
        print(f"Error exporting tables to JSON: {e}")

def import_all_tables_from_json(json_path="database_export.json"):
    """
    Imports all rows from a JSON file into their corresponding tables.
    WARNING: This will DELETE existing rows in those tables!
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)

        conn, cursor = open_connection()

        for table, rows in import_data.items():
            print(f"Importing table: {table} ({len(rows)} rows)")

            # Delete existing data in this table
            cursor.execute(f"DELETE FROM {table}")

            if not rows:
                continue

            # Determine columns from the first row
            columns = list(rows[0].keys())
            col_str = ', '.join(columns)
            placeholders = ', '.join(['?'] * len(columns))

            for row in rows:
                # Check for missing or extra keys
                if set(row.keys()) != set(columns):
                    print(f"Warning: Row keys in {table} do not match the first row. This row will be skipped: {row}")
                    continue
                values = [row[col] for col in columns]
                cursor.execute(
                    f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})",
                    values
                )

        conn.commit()
        close_connection(conn)
        print("All tables have been imported from", json_path)
    except Exception as e:
        print(f"Error importing tables from JSON: {e}")

# ===========================================================================================================

def create_frage(bez: str, text: str, bem: str, ja: int, nein: int, unsicher: int, initial: bool):
    conn = None

    try:
        conn, cursor = open_connection()
        element_id: int = get_next_id()
        create_element(1, element_id)

        if initial:
            cursor.execute("UPDATE tbl_fragen SET Initial = 0 WHERE Initial = 1")

        cursor.execute("INSERT INTO tbl_fragen (ID, Bez, Text, Bem, Ja, Nein, Unsicher, Initial) VALUES ("
                       "?, ?, ?, ?, ?, ?, ?, ?);", (element_id, bez, text, bem, ja, nein, unsicher, initial))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def get_all_fragen():
    """Fetches all questions with ID, Bez and Text from tbl_fragen."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez, Text FROM tbl_fragen ORDER BY Bez COLLATE NOCASE ASC")
    fragen = cursor.fetchall()
    close_connection(conn)

    return [
        {"ID": row[0], "Bez": row[1], "Text": row[2]}
        for row in fragen
    ]

def get_frage_by_id(frage_id: int):
    """Fetches a single frage by ID."""
    conn, cursor = open_connection()
    cursor.execute("SELECT Bez, Text, Bem, Ja, Nein, Unsicher, Initial FROM tbl_fragen WHERE ID = ?", (frage_id,))
    frage = cursor.fetchone()
    close_connection(conn)

    if frage:
        return {"Bez": frage[0], "Text": frage[1], "Bem": frage[2], "Ja": frage[3], "Nein": frage[4], "Unsicher": frage[5], "Initial": frage[6]}
    return None

def get_initial_frage():
    conn, cursor = open_connection()
    cursor.execute("SELECT ID FROM tbl_fragen WHERE Initial = 1")
    row = cursor.fetchone()
    close_connection(conn)
    if not row:
        return None

    frage_id = row[0]
    # Find the element with table_id=1 (Frage), foreign_id=frage_id
    conn, cursor = open_connection()
    cursor.execute("SELECT ID FROM tbl_elemente WHERE table_id = 1 AND foreign_id = ?", (frage_id,))
    row = cursor.fetchone()
    close_connection(conn)
    if not row:
        return None
    element_id = row[0]
    return get_element_by_id(element_id)

def update_frage(frage_id: int, bez: str, text: str, bem: str, ja: int, nein: int, unsicher: int, initial: bool):
    """Updates an existing frage."""
    conn, cursor = open_connection()

    if initial:
        cursor.execute("UPDATE tbl_fragen SET Initial = 0 WHERE Initial = 1")

    cursor.execute("""
        UPDATE tbl_fragen SET Bez = ?, Text = ?, Bem = ?, Ja = ?, Nein = ?, Unsicher = ?, Initial = ? WHERE ID = ?
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

def get_all_fragen_for_dropdown():
    """Return Fragen as 'Bez: Text', sorted alphabetically by Bez (case-insensitive)."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez, Text FROM tbl_fragen ORDER BY Bez COLLATE NOCASE ASC")
    rows = cursor.fetchall()
    close_connection(conn)
    return [{"ID": r[0], "Bez": r[1], "Text": r[2], "Display": f"{r[1]}: {r[2]}"} for r in rows]

def get_all_elements_with_edges():
    """
    Return all elements (Frage/Antwort/Prompt) with their Bez and, for Fragen, their edges.
    Uses tbl_elemente.ID as the canonical node id.
    """
    conn, cursor = open_connection()
    cursor.execute("""
        SELECT
            e.ID            AS ElementID,
            e.table_id      AS TableID,
            e.foreign_id    AS ForeignID,
            CASE
              WHEN e.table_id = 1 THEN f.Bez
              WHEN e.table_id = 2 THEN a.Bez
              WHEN e.table_id = 3 THEN p.Bez
            END             AS Bez,
            f.Ja            AS Ja,
            f.Nein          AS Nein,
            f.Unsicher      AS Unsicher,
            f.Initial       AS Initial
        FROM tbl_elemente e
        LEFT JOIN tbl_fragen    f ON e.table_id = 1 AND f.ID = e.foreign_id
        LEFT JOIN tbl_antworten a ON e.table_id = 2 AND a.ID = e.foreign_id
        LEFT JOIN tbl_prompts   p ON e.table_id = 3 AND p.ID = e.foreign_id
        ORDER BY Bez COLLATE NOCASE ASC
    """)
    rows = cursor.fetchall()
    close_connection(conn)

    results = []
    for r in rows:
        results.append({
            "ElementID": r[0],
            "TableID": r[1],          # 1=Frage, 2=Antwort, 3=Prompt
            "ForeignID": r[2],
            "Bez": r[3] or "",
            "Ja": r[4],
            "Nein": r[5],
            "Unsicher": r[6],
            "Initial": r[7] if r[7] is not None else 0,  # 0/1 from SQLite
        })
    return results

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
    """Fetches all antwort IDs, names and text from tbl_antworten."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez, Text FROM tbl_antworten ORDER BY Bez COLLATE NOCASE ASC")
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

def create_prompt(bez: str, frage: str, dsgvo: str):
    conn = None
    try:
        conn, cursor = open_connection()
        element_id: int = get_next_id()
        create_element(3, element_id)

        cursor.execute(
            "INSERT INTO tbl_prompts (ID, Bez, Frage, DSGVO) VALUES (?, ?, ?, ?);",
            (element_id, bez, frage, dsgvo)
        )

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)

def get_all_prompts():
    """Fetches all prompts for listing/dropdowns."""
    conn, cursor = open_connection()
    cursor.execute("SELECT ID, Bez, Frage, DSGVO FROM tbl_prompts ORDER BY Bez COLLATE NOCASE ASC")
    prompts = cursor.fetchall()
    close_connection(conn)

    return [
        {"ID": row[0], "Bez": row[1], "Frage": row[2], "DSGVO": row[3]}
        for row in prompts
    ]

def get_prompt_by_id(prompt_id):
    """Fetches a single prompt by ID."""
    conn, cursor = open_connection()
    cursor.execute("SELECT Bez, Frage, DSGVO FROM tbl_prompts WHERE ID = ?", (prompt_id,))
    prompt = cursor.fetchone()
    close_connection(conn)

    if prompt:
        return {"Bez": prompt[0], "Frage": prompt[1], "DSGVO": prompt[2]}
    return None

def update_prompt(prompt_id, bez, frage, dsgvo):
    """Updates an existing prompt."""
    conn, cursor = open_connection()
    cursor.execute("""
        UPDATE tbl_prompts SET Bez = ?, Frage = ?, DSGVO = ? WHERE ID = ?
    """, (bez, frage, dsgvo, prompt_id))
    conn.commit()
    close_connection(conn)

def delete_prompt(prompt_id):
    """Deletes a prompt from tbl_prompts based on the given ID."""
    conn, cursor = open_connection()
    delete_element(prompt_id)
    cursor.execute("DELETE FROM tbl_prompts WHERE ID = ?", (prompt_id,))
    conn.commit()
    close_connection(conn)

def prompt_is_referenced(prompt_id: int) -> bool:
    conn, cursor = open_connection()
    cursor.execute("""
        SELECT COUNT(*) FROM tbl_fragen
        WHERE Ja = ? OR Nein = ? OR unsicher = ?
    """, (prompt_id, prompt_id, prompt_id))
    count = cursor.fetchone()[0]
    close_connection(conn)
    return count > 0

# ===========================================================================================================

def set_email_config(email_recipient: str, email_subject: str, email_body: str):
    """
    Stores email configuration in tbl_config.
    Always uses ID = 1 (single configuration row).
    Inserts if not existing, updates otherwise.
    """
    conn, cursor = open_connection()
    try:
        # Check if row with ID=1 exists
        cursor.execute("SELECT COUNT(*) FROM tbl_config WHERE ID = 1")
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("""
                UPDATE tbl_config
                SET email_recipient = ?, email_subject = ?, email_body = ?
                WHERE ID = 1
            """, (email_recipient, email_subject, email_body))
        else:
            cursor.execute("""
                INSERT INTO tbl_config (ID, email_recipient, email_subject, email_body)
                VALUES (1, ?, ?, ?)
            """, (email_recipient, email_subject, email_body))

        conn.commit()
    finally:
        close_connection(conn)

def get_email_config():
    """
    Returns the email configuration from tbl_config (ID = 1).
    """
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT email_recipient, email_subject, email_body
            FROM tbl_config
            WHERE ID = 1
        """)
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "email_recipient": row[0] or "",
            "email_subject": row[1] or "",
            "email_body": row[2] or ""
        }
    finally:
        close_connection(conn)

def set_llm_config(
    provider: str,
    ollama_base_url: str,
    ollama_model: str,
    openai_api_key: str,
    openai_model: str,
    openai_base_url: str,
    temperature: float,
    max_output_tokens: int
):
    """
    Stores LLM configuration in tbl_llm_config.
    Always uses ID = 1.
    """
    conn, cursor = open_connection()
    try:
        cursor.execute("SELECT COUNT(*) FROM tbl_llm_config WHERE ID = 1")
        exists = cursor.fetchone()[0]

        provider = provider or "ollama"
        ollama_base_url = ollama_base_url or "http://localhost:11434"
        ollama_model = ollama_model or "llama3.1"
        openai_model = openai_model or "gpt-4.1-mini"

        if exists:
            cursor.execute("""
                UPDATE tbl_llm_config
                SET provider = ?,
                    ollama_base_url = ?,
                    ollama_model = ?,
                    openai_api_key = ?,
                    openai_model = ?,
                    openai_base_url = ?,
                    temperature = ?,
                    max_output_tokens = ?
                WHERE ID = 1
            """, (
                provider,
                ollama_base_url,
                ollama_model,
                openai_api_key,
                openai_model,
                openai_base_url,
                temperature,
                max_output_tokens
            ))
        else:
            cursor.execute("""
                INSERT INTO tbl_llm_config (
                    ID,
                    provider,
                    ollama_base_url,
                    ollama_model,
                    openai_api_key,
                    openai_model,
                    openai_base_url,
                    temperature,
                    max_output_tokens
                )
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provider,
                ollama_base_url,
                ollama_model,
                openai_api_key,
                openai_model,
                openai_base_url,
                temperature,
                max_output_tokens
            ))

        conn.commit()
    finally:
        close_connection(conn)


def get_llm_config():
    """
    Returns LLM configuration from tbl_llm_config.
    If no row exists, returns safe defaults.
    """
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT
                provider,
                ollama_base_url,
                ollama_model,
                openai_api_key,
                openai_model,
                openai_base_url,
                temperature,
                max_output_tokens
            FROM tbl_llm_config
            WHERE ID = 1
        """)
        row = cursor.fetchone()

        if not row:
            return {
                "provider": "ollama",
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llama3.1",
                "openai_api_key": "",
                "openai_model": "gpt-4.1-mini",
                "openai_base_url": "",
                "temperature": 0.2,
                "max_output_tokens": 1000
            }

        return {
            "provider": row[0] or "ollama",
            "ollama_base_url": row[1] or "http://localhost:11434",
            "ollama_model": row[2] or "llama3.1",
            "openai_api_key": row[3] or "",
            "openai_model": row[4] or "gpt-4.1-mini",
            "openai_base_url": row[5] or "",
            "temperature": row[6] if row[6] is not None else 0.2,
            "max_output_tokens": row[7] if row[7] is not None else 1000
        }
    finally:
        close_connection(conn)


def get_llm_config_safe():
    """
    Same as get_llm_config(), but masks the API key for UI display.
    """
    cfg = get_llm_config()
    api_key = cfg.get("openai_api_key") or ""

    cfg["openai_api_key_set"] = bool(api_key)
    cfg["openai_api_key"] = ""

    return cfg

def create_contact_request(data: dict) -> int:
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            INSERT INTO tbl_contact_requests (
                organisation_name,
                organisation_location,
                contact_person,
                phone_extension,
                email,
                product_description,
                product_purpose,
                development_stage,
                data_categories_processing_output,
                specific_questions_problems,
                participation_timeline
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("organisation_name", ""),
            data.get("organisation_location", ""),
            data.get("contact_person", ""),
            data.get("phone_extension", ""),
            data.get("email", ""),
            data.get("product_description", ""),
            data.get("product_purpose", ""),
            data.get("development_stage", ""),
            data.get("data_categories_processing_output", ""),
            data.get("specific_questions_problems", ""),
            data.get("participation_timeline", "")
        ))

        contact_id = cursor.lastrowid
        conn.commit()
        return contact_id
    finally:
        close_connection(conn)


def get_all_contact_requests():
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT
                ID,
                created_at,
                organisation_name,
                organisation_location,
                contact_person,
                phone_extension,
                email,
                product_description,
                product_purpose,
                development_stage,
                data_categories_processing_output,
                specific_questions_problems,
                participation_timeline
            FROM tbl_contact_requests
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        keys = [
            "ID", "created_at", "organisation_name", "organisation_location",
            "contact_person", "phone_extension", "email", "product_description",
            "product_purpose", "development_stage",
            "data_categories_processing_output", "specific_questions_problems",
            "participation_timeline"
        ]

        return [dict(zip(keys, row)) for row in rows]
    finally:
        close_connection(conn)


def set_contact_notification_config(recipient: str, subject: str, body: str):
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            INSERT INTO tbl_contact_notification_config (ID, recipient, subject, body)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(ID) DO UPDATE SET
                recipient = excluded.recipient,
                subject = excluded.subject,
                body = excluded.body
        """, (recipient, subject, body))
        conn.commit()
    finally:
        close_connection(conn)


def get_contact_notification_config():
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT recipient, subject, body
            FROM tbl_contact_notification_config
            WHERE ID = 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        return {"recipient": row[0] or "", "subject": row[1] or "", "body": row[2] or ""}
    finally:
        close_connection(conn)


def set_contact_company_email_config(subject: str, body: str):
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            INSERT INTO tbl_contact_company_email_config (ID, subject, body)
            VALUES (1, ?, ?)
            ON CONFLICT(ID) DO UPDATE SET
                subject = excluded.subject,
                body = excluded.body
        """, (subject, body))
        conn.commit()
    finally:
        close_connection(conn)


def get_contact_company_email_config():
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT subject, body
            FROM tbl_contact_company_email_config
            WHERE ID = 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        return {"subject": row[0] or "", "body": row[1] or ""}
    finally:
        close_connection(conn)


def set_smtp_config(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    use_tls: bool
):
    conn, cursor = open_connection()
    try:
        cursor.execute("SELECT COUNT(*) FROM tbl_smtp_config WHERE ID = 1")
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("""
                UPDATE tbl_smtp_config
                SET smtp_host = ?,
                    smtp_port = ?,
                    smtp_user = ?,
                    smtp_password = ?,
                    smtp_from = ?,
                    use_tls = ?
                WHERE ID = 1
            """, (
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_password,
                smtp_from,
                int(use_tls)
            ))
        else:
            cursor.execute("""
                INSERT INTO tbl_smtp_config (
                    ID,
                    smtp_host,
                    smtp_port,
                    smtp_user,
                    smtp_password,
                    smtp_from,
                    use_tls
                )
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_password,
                smtp_from,
                int(use_tls)
            ))

        conn.commit()
    finally:
        close_connection(conn)


def get_smtp_config():
    conn, cursor = open_connection()
    try:
        cursor.execute("""
            SELECT smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, use_tls
            FROM tbl_smtp_config
            WHERE ID = 1
        """)
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "smtp_host": row[0] or "",
            "smtp_port": row[1] or 587,
            "smtp_user": row[2] or "",
            "smtp_password": row[3] or "",
            "smtp_from": row[4] or "",
            "use_tls": bool(row[5])
        }
    finally:
        close_connection(conn)


def get_smtp_config_safe():
    cfg = get_smtp_config()
    if not cfg:
        return {
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": "",
            "smtp_password_set": False,
            "smtp_from": "",
            "use_tls": True
        }

    password = cfg.get("smtp_password") or ""
    cfg["smtp_password_set"] = bool(password)
    cfg["smtp_password"] = ""
    return cfg


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
    init_db()
    # admin_nuke_database()
    # admin_clean_all()
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

    # print(get_element_by_id(1))
    # print(get_element_by_id(4))
    # print(get_element_by_id(2))

    # save_all_tables_to_json()
    # import_all_tables_from_json()

    # set_email_config("datenschutz-sandbox@lfdi.de", "Kontaktaufnahme: Datenschutz-Sandbox", "Hallo")
