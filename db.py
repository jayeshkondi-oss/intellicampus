import pymysql
import pymysql.cursors
from pymysql import converters
from pymysql.constants import FIELD_TYPE
from flask import g, current_app
import os

def get_db():
    if 'db' not in g:
        time_converters = converters.conversions.copy()
        time_converters[FIELD_TYPE.TIME] = converters.convert_time
        g.db = pymysql.connect(
    host=current_app.config['MYSQL_HOST'],
    port=int(os.environ.get('MYSQL_PORT', 3306)),
    user=current_app.config['MYSQL_USER'],
    password=current_app.config['MYSQL_PASSWORD'],
    database=current_app.config['MYSQL_DB'],
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
    conv=time_converters,
    connect_timeout=30,
    ssl_disabled=False
)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)