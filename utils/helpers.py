"""Utility helpers shared across blueprints."""
import os, uuid
from werkzeug.utils import secure_filename
from config import Config

def save_file(file_obj, prefix='file'):
    """Save an uploaded file and return its stored filename, or None."""
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return None
    fname = f"{prefix}_{uuid.uuid4().hex}.{ext}"
    file_obj.save(os.path.join(Config.UPLOAD_FOLDER, fname))
    return fname

def grade_from_marks(marks, max_marks):
    """Auto-compute a grade from marks percentage."""
    if marks is None or max_marks is None or max_marks == 0:
        return ''
    pct = (marks / max_marks) * 100
    if pct >= 90: return 'O'
    if pct >= 80: return 'A+'
    if pct >= 70: return 'A'
    if pct >= 60: return 'B+'
    if pct >= 50: return 'B'
    if pct >= 45: return 'C'
    if pct >= 40: return 'D'
    return 'F'
