import sqlite3

def conn_fac():
    return sqlite3.connect("faptrack.db")