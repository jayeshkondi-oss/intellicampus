import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY       = os.getenv('SECRET_KEY', 'erp-dev-secret-change-in-production')
    MYSQL_HOST       = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER       = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD   = os.getenv('MYSQL_PASSWORD', 'jay30')
    MYSQL_DB         = os.getenv('MYSQL_DB', 'college_erp')
    UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc'}
