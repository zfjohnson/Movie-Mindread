import mysql.connector
import sys
from mysql.connector import errorcode

try:
    database = mysql.connector.connect(
        host="localhost",
        user="moviemindread",
        passwd="movies",
        use_pure=True
    )
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:        
    cursorObject = database.cursor()
    if sys.argv[1]:
        if sys.argv[1] == "create":
            cursorObject.execute("CREATE DATABASE movie_mindread;")
        elif sys.argv[1] == "drop":
            cursorObject.execute("DROP DATABASE IF EXISTS movie_mindread;")

    rows = cursorObject.fetchall()
    for row in rows:
        print(row)