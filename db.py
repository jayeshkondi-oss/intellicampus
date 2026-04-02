"""
Database helper — uses PyMySQL (pure Python, no C compiler needed).
Provides get_db() which returns a connection with DictCursor.
"""
import pymysql
import pymysql.cursors
from pymysql import converters
from pymysql.constants import FIELD_TYPE
from flask import g, current_app

def get_db():
    """Return a per-request PyMySQL connection (stored in Flask's g)."""
    if 'db' not in g:
        # Treat TIME columns as time-of-day values for template strftime usage.
        time_converters = converters.conversions.copy()
        time_converters[FIELD_TYPE.TIME] = converters.convert_time
        g.db = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            conv=time_converters
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
