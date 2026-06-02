import os
from dotenv import load_dotenv

load_dotenv("config.env")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "nepXpress")
