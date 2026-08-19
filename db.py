import psycopg2
from psycopg2 import sql

HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "juanpa"
DATABASE = "ejercicio_kiro"

try:
    print("Conectando a PostgreSQL...")

    conexion = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database="postgres"
    )

    print("Conexion exitosa.")

    conexion.autocommit = True
    cursor = conexion.cursor()

    print("Creando base de datos...")

    cursor.execute(
        sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DATABASE)
        )
    )

    print("Base de datos creada correctamente.")

    cursor.close()
    conexion.close()

except psycopg2.errors.DuplicateDatabase:
    print("La base de datos ya existe.")

except Exception as e:
    print("Ocurrio un error.")
    print(type(e))
    print(repr(e))