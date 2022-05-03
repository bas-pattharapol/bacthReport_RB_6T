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

server = "172.30.1.211"
database = "RB_2T"
username = "sa"
password = "12345678"

cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+ server +';DATABASE='+database+';UID='+username+';PWD='+password)
test1 = cnxn.cursor()
test1.execute("""             
               SELECT * from BatchHistory.dbo.BatchDetail WHERE Batch_Log_ID = '1J7YFPJS2T' AND Action_CD = '234' AND (UnitOrConnection = 'MX101' or UnitOrConnection LIKE 'T%_MX101' or UnitOrConnection LIKE 'MX101_%')
                        """) 

col = []
row = []
t = []

for s1 in test1 :
    col.append(s1[6])
#print(col)
t = []
count = 0
for c in range(len(col)):
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+ server +';DATABASE='+database+';UID='+username+';PWD='+password)
    test2 = cnxn.cursor()
    test2.execute("""             
                SELECT DateTime  , Phase_Instance_ID , Phase_ID  ,Actual_Value ,Target_Value FROM BatchHistory.dbo.ProcessVar WHERE Batch_Log_ID = '1J7YFPJS2T'  AND (UnitOrConnection = 'MX101' or UnitOrConnection LIKE 'T%_MX101' or UnitOrConnection LIKE 'MX101_%')
                """) 
    count = 0
    PreId = True
    for s2 in test2:
        if col[c] == s2[1]:
            if PreId :
                t.append(s2[1])
                PreId = False
            t.append(s2[3])
            t.append(s2[4])
            count += 1
       
    #t.append(col[c]) 
    if count < 10:
        for i in range(count, 10):
            t.append("-")  
            t.append("-") 
    #t.append(col[c])     
    row.append(t)
    
    t = []
       
           
print(row)