from src.database.dbconnpool import DatabaseConnectionPool

# Create a global connection pool object
connection_pool = DatabaseConnectionPool(max_connections=5)

# Initialize the connection pool
def init_connection_pool():
    global connection_pool

# Function to get the connection from the pool
def get_connection_from_pool():
    return connection_pool.get_connection()

# Function to release the connection back to the pool
def release_connection_to_pool(connection):
    connection_pool.put_connection(connection)