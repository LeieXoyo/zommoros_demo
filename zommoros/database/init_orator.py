from zommoros.database import orator as config

from orator import DatabaseManager, Model

db = DatabaseManager(config.DATABASES)
Model.set_connection_resolver(db)
