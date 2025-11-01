import threading
import sqlite3
import os

db_directory = os.path.join(os.getcwd(), 'db')
dbPath = os.path.join(db_directory, 'vm.db')

# SQL statements to create tables if they don't exist
CREATE_TABLE_ADS = """
CREATE TABLE IF NOT EXISTS ads (
    id TEXT NOT NULL,
    ads TEXT NOT NULL,
    version TEXT NOT NULL
)
"""

CREATE_TABLE_INFO = """
CREATE TABLE IF NOT EXISTS info (
    info_no TEXT NOT NULL,
    info_comment TEXT NOT NULL
)
"""

CREATE_TABLE_LANGUAGE = """
CREATE TABLE IF NOT EXISTS language_list (
    language_id TEXT NOT NULL,
    language_name TEXT NOT NULL,
    language_icon TEXT NOT NULL,
    version TEXT NOT NULL
)
"""

CREATE_TABLE_LANGUAGEVALUE = """
CREATE TABLE IF NOT EXISTS language_value (
    lang_key TEXT NOT NULL,
    lang_value TEXT NOT NULL,
    lang_type TEXT NOT NULL
)
"""

CREATE_TABLE_PRODUCT = """
CREATE TABLE IF NOT EXISTS product (
    id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_name_de TEXT NOT NULL,
    price INTEGER NOT NULL,
    currency TEXT NOT NULL,
    description TEXT NOT NULL,
    description_de TEXT NOT NULL,
    category TEXT NOT NULL,
    theme TEXT NOT NULL,
    additional_info1 TEXT NOT NULL,
    additional_info2 TEXT NOT NULL,
    additional_info3 TEXT NOT NULL,
    additional_info4 TEXT NOT NULL,
    additional_info5 TEXT NOT NULL,
    additional_info1_de TEXT NOT NULL,
    additional_info2_de TEXT NOT NULL,
    additional_info3_de TEXT NOT NULL,
    additional_info4_de TEXT NOT NULL,
    additional_info5_de TEXT NOT NULL,
    thumbnail TEXT NOT NULL,
    subinfoimage1 TEXT,
    subinfoimage2 TEXT,
    subinfoimage3 TEXT,
    stock INTEGER NOT NULL,
    box INTEGER NOT NULL,
    version TEXT NOT NULL
)
"""

def create_database_connection():
    try:
        conn = sqlite3.connect(dbPath)
        sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
        
        threadsafety = conn.execute(
            """
            select * from pragma_compile_options
            where compile_options like 'THREADSAFE=%'
            """
        ).fetchone()[0]
        print(threadsafety)
        conn.close()

        threadsafety_value = int(threadsafety.split("=")[1])

        if sqlite_threadsafe2python_dbapi[threadsafety_value] == 3:
            check_same_thread = False
        else:
            check_same_thread = True

        conn = sqlite3.connect(dbPath, check_same_thread=check_same_thread)

        return conn
    except sqlite3.Error as error:
        print('db connection error', error)

class DatabaseConnectionPool:
    def __init__(self, max_connections):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

        # Create tables if they don't exist
        self._create_tables()

    def _create_tables(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(CREATE_TABLE_ADS)
            cursor.execute(CREATE_TABLE_INFO)
            cursor.execute(CREATE_TABLE_LANGUAGE)
            cursor.execute(CREATE_TABLE_LANGUAGEVALUE)
            cursor.execute(CREATE_TABLE_PRODUCT)
            conn.commit()
        finally:
            cursor.close()
            self.put_connection(conn)

    def get_connection(self):
        with self.lock:
            if len(self.connections) < self.max_connections:
                new_connection = create_database_connection()
                self.connections.append(new_connection)
                return new_connection
            else:
                raise RuntimeError("[VM/dbconnpool]: ERR: Connection pool limit reached")

    def put_connection(self, connection):
        with self.lock:
            self.connections.remove(connection)
