from .repository import BaseRepository
from .connection import Database
repository = BaseRepository(Database())