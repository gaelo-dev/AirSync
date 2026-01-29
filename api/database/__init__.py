from typing import Optional, Any
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from flask import g, current_app
import functools
import click

from .types import *

def transactional(multiple: bool = False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self: Access, *args, **kwargs) -> Any:
            # Extraemos el SQL del docstring de la función
            sql = func.__doc__
            if not sql:
                raise ValueError(f"La función {func.__name__} necesita un docstring con el SQL")

            payload = args[0] if args else kwargs
            try:
                with self._conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(sql, payload)
                    if cur.description: 
                        result = cur.fetchall() if multiple else cur.fetchone()
                    else:
                        result = None

                    self._conn.commit()
                    return result
            except Exception as e:
                self._conn.rollback()
                print(f"Error en query {func.__name__}: {e}")
                raise e
            
        return wrapper
    
    return decorator

class Client:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None

    def init_app(self, app):
        """Inicializa el pool usando la configuración de la app"""
        conn_str = app.config['DATABASE']
        self.pool = ConnectionPool(conn_str)

        # Registrar funciones de limpieza
        app.teardown_appcontext(self.teardown)
        app.cli.add_command(create_tables_command)

    def teardown(self, e=None):
        """Elimina la instancia `Access` y devuelve la conexión vinculada al pool"""
        db_access = g.pop('db_access', None)
        
        if db_access is not None:
            self.pool.putconn(db_access._conn)

    @property
    def access(self) -> Access:
        """Retorna una instancia `Access` que esta vinculada a la conexión que se obtenga del pool"""
        if 'db_access' not in g:
            conn = self.pool.getconn()
            g.db_access = Access(conn)
        
        return g.db_access

class Access:
    def __init__(self, conn: Connection):
        self._conn = conn

    def execute_file(self, name: str) -> None:
        """Ejecuta un archivo `.sql` que este dentro de la carpeta `database/queries`"""
        with self._conn.cursor() as cur:
            with current_app.open_resource(f"database/queries/{name}.sql") as f: 
                cur.execute(f.read().decode("utf8"))
            
            self._conn.commit()
    
    def create_tables(self) -> None:
        self.execute_file("schema")
    
    @transactional()
    def create_device(self, payload: DeviceCreate) -> Device:
        """
        INSERT INTO devices (name, api_key) 
        VALUES (%(name)s, %(api_key)s)
        RETURNING *;
        """
        pass
        
    @transactional(multiple=True)
    def fetch_devices(self) -> list[Device]:
        """
        SELECT * FROM devices;
        """
        pass
    
    @transactional()
    def fetch_device_by_id(self, *, id: DeviceId) -> Optional[Device]:
        """
        SELECT * FROM devices
        WHERE id = %(id)s
        LIMIT 1;
        """
        pass
        
    @transactional()
    def record_reading(self, payload: ReadingCreate) -> None:
        """
        INSERT INTO readings (device_id, temp, humidity, pm10, gas)
        VALUES (%(device_id)s, %(temp)s, %(humidity)s, %(pm10)s, %(gas)s)
        """
        pass

db_client = Client()
init_app = db_client.init_app

@click.command("create-tables")
def create_tables_command():
    """Crea las tablas usando el archivo schema.sql"""
    db_client.access.create_tables()
    click.echo("✅ Base de datos inicializada correctamente.")
