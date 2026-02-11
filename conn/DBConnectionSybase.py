import pyodbc
import configparser
import os
import sys

class DBConnectionSybase:
    def __init__(self):
        try:
            self.conn = self.create_connection()
        except pyodbc.Error as e:
            print("Error al conectar a la base de datos:", e)
            self.conn = None
        except configparser.Error as e:
            print("Error al leer el archivo de configuración:", e)
            self.conn = None
        except Exception as e:
            print("Error inesperado:", e)
            self.conn = None

    def create_connection(self):
        # Buscar config.ini en el mismo directorio que el ejecutable o el script
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_path, '../config.ini')
        print(f"[DEBUG] Buscando config.ini en: {config_path}")
        print(f"[DEBUG] Archivos en {base_path}: {os.listdir(base_path)}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No se encontró config.ini en {config_path}")
        config = configparser.ConfigParser()
        read_files = config.read(config_path)
        if not read_files:
            raise FileNotFoundError(f"No se pudo leer config.ini en {config_path}")
        self.serv = config['CONEXION']['serv']
        self.usr = config['CONEXION']['usr']
        self.passwd = config['CONEXION']['passwd']
        self.db = config['CONEXION']['db']
        self.prt = config['CONEXION']['prt']
        self.nombreCliente = config['EMPRESA']['nombre']
        self.token = config['TOKEN']['TOKEN']
        """
         print("--> "+self.serv)
        print("--> "+self.passwd)
        print("--> "+self.db)
        print("--> "+self.prt)
        print("--> "+self.nombreCliente)
        print("--> "+self.usr)
        print("--> "+self.token)
         """
        conn = pyodbc.connect('DSN=' + self.serv + ';Database=' + self.db + ';UID=' + self.usr + ';PWD=' + self.passwd, autocommit=True)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin1')
        conn.setencoding('latin1')

        return conn
