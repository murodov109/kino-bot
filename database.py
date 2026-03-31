import sqlite3
from sqlite3 import Error

class Database:
    def __init__(self, db_file):
        """ create a database connection to a SQLite database """
        self.connection = None
        try:
            self.connection = sqlite3.connect(db_file)
        except Error as e:
            print(e)

    def close(self):
        if self.connection:
            self.connection.close()

class Film:
    def __init__(self, title, director, release_year):
        self.title = title
        self.director = director
        self.release_year = release_year

class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email

class Channel:
    def __init__(self, name, description):
        self.name = name
        self.description = description

class PremiumSettings:
    def __init__(self, user_id, expiry_date):
        self.user_id = user_id
        self.expiry_date = expiry_date

if __name__ == '__main__':
    db = Database('kino_bot.db')  
    db.close()  
