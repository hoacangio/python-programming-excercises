import os

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DATABASE", "QLNhanVien"),
}


def get_connection() -> MySQLConnection:
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Loi ket noi MySQL: {e}")
        return None
