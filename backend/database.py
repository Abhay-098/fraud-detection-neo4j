import os
from contextlib import contextmanager
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

@contextmanager
def session():
    s = driver.session(database=DATABASE)
    try:
        yield s
    finally:
        s.close()

def verify_connection():
    with session() as s:
        return s.run("RETURN 1 AS ok").single()["ok"] == 1
