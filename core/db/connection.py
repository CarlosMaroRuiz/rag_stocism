import mysql.connector
from core.enviroment import env


class Database:
    def __init__(self):
        self.config = {
            "host": env.MYSQL_HOST,
            "user": env.MYSQL_USER,
            "password": env.MYSQL_PASSWORD,
            "database": env.MYSQL_DATABASE,
            "port": env.MYSQL_PORT,
        }

    def connect(self):
        return mysql.connector.connect(**self.config)
