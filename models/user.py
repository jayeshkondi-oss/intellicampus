from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, row):
        self.id        = row['id']
        self.email     = row['email']
        self.role      = row['role']
        self.full_name = row['full_name']
        self.avatar    = row.get('avatar')
