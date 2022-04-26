from flask import Flask, render_template, request, redirect, url_for, jsonify,make_response,session
from flask.sessions import NullSession
import flask_login
from flask_login.utils import logout_user
import pyodbc
import pdfkit
from datetime import timedelta
import time

app = Flask(__name__)

app.secret_key = '0'
login_manager = flask_login.LoginManager()

login_manager.init_app(app)
users = {}
nameUser = None

server = "172.30.1.1"
database = "RB_6T"
username = "sa"
password = "P@ssw0rd"

cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+ server +';DATABASE='+database+';UID='+username+';PWD='+password)
test1 = cnxn.cursor()
test1.execute("""             
                SELECT DISTINCT Phase_Instance_ID , DateTime FROM BatchHistory.dbo.ProcessVar 
                WHERE (UnitOrConnection = 'MX101' or UnitOrConnection LIKE 'T%_MX101' or UnitOrConnection LIKE 'MX101_%') AND Batch_Log_ID = '1J7YFPJS2T'
                ORDER BY DateTime ASC; 
                        """) 
col = []
for s1 in test1:
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+ server +';DATABASE='+database+';UID='+username+';PWD='+password)
    test2 = cnxn.cursor()
    test2.execute("""
                            SELECT Actual_Value ,Target_Value FROM BatchHistory.dbo.ProcessVar 
                            WHERE Phase_Instance_ID = ?
                            ORDER BY DateTime ASC; 
                            """,(s1[0],)) 
   
    row = []
    for i in test2: 
        row.append(i[0])
        row.append(i[1])
    print(len(row))
    if len(row) < 20 :
        for i in range(len(row),20,1):
            row.append(' ')
    col.append(row)
print(col)
print(len(col))