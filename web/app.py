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


class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('Username')
    if email not in users:
        return

    user = User()
    user.id = email
    return user
    
@app.errorhandler(401)
def custom_401(error):
    return redirect(url_for('login'))

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    

@app.route('/')
@app.route('/login', methods=["GET","POST"])
def login():
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    SQL_Login = cnxn.cursor()
    SQL_Login.execute("SELECT username ,password FROM Login ")

    global users

    for i in SQL_Login:
        users[i[0]] = {'Password' : i[1]}

    print(users)
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['Username']
   
    if request.form['Password'] == users[email]['Password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
            
        global nameUser 
        nameUser = email
            

        return redirect(url_for('select'))
           
   
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/select')
@flask_login.login_required
def select():
    
    return render_template('select.html',nameUser=nameUser)

@app.route('/overview/<string:name>', methods=['GET', 'POST'])
@flask_login.login_required
def deleteList(name):
   
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    overview = cnxn.cursor()
    overview.execute("""
                     SELECT bil.Batch_Log_ID , bil.Campaign_ID,bil.Lot_ID,bil.Batch_ID,bil.Product_ID,bil.Product_Name,bil.Recipe_ID,bil.Recipe_Name,bil.Batch_Size,MIN(pv.[DateTime]) as StartDateTime , MAX(pv.[datetime]) as StopDateTime
                        FROM  BatchHistory.dbo.BatchIdLog bil 
                        inner join BatchHistory.dbo.ProcessVar pv 
                        ON bil.Batch_Log_ID = pv.Batch_Log_ID AND bil.Batch_Log_ID = ?
                        GROUP BY bil.Batch_Log_ID , bil.Campaign_ID,bil.Lot_ID,bil.Batch_ID,bil.Product_ID,bil.Product_Name,bil.Recipe_ID,bil.Recipe_Name,bil.Batch_Size;
                        """,(name,))
       #for i in cursor:
    #    print(i)
    return render_template('overview.html',data=overview,nameUser=nameUser)

@app.route('/overview_CIP/<string:name>/<string:db>/<string:id>', methods=['GET', 'POST'])
@flask_login.login_required
def deleteList_CIP(name,db,id):
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    overview_CIP = cnxn.cursor()
    overview_CIP.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM "+db+" WHERE End_Time LIKE '%:%' AND Batch_No ='"+name+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")

       #for i in cursor:
    if db == "MM_CIP_Report":
        st = "Mian Mixer CIP Report"
    elif db == "PM_CIP_Report":
        st = "Pre Mixer CIP Report"
    elif db == "ST_CIP_Report":
        st = "Storage Tank CIP Report"
    else :
        st = db


    #    print(i)
    return render_template('overview_CIP.html',data=overview_CIP,name=name,nameUser=nameUser,db=db,id=id,st =st)

@app.route('/bacth_CIP/<string:name>/<string:db>/<string:id>', methods=['GET', 'POST'])
@flask_login.login_required
def bacth_CIP(name,db,id):
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    bacth_CIP  = cnxn.cursor()
    bacth_CIP.execute("SELECT * FROM " + db +"  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name +"' ORDER BY Recipe_Step ASC ")

    if db == "MM_CIP_Report":
        st = "Mian Mixer CIP Report"
    elif db == "PM_CIP_Report":
        st = "Pre Mixer CIP Report"
    elif db == "ST_CIP_Report":
        st = "Storage Tank CIP Report"
    else :
        st = db
     
       #for i in cursor:
    #    print(i)
    return render_template('bacth_CIP.html',data=bacth_CIP,nameUser=nameUser,name=name,db=db,id=id,st=st)

@app.route('/Validation_CIP/<string:name>/<string:db>/<string:id>', methods=['GET', 'POST'])
@flask_login.login_required
def Validation_CIP(name,db,id):

    if db == "MM_CIP_Report":
        st = "SQL_CIP_MM_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_MM")
        Validation_CIP.execute("INSERT Into User_MM ([Date] ,[Time] ,Batch_No,MM_CIP_Recipe_Step ,MM_CIP_Temp,MM_CIP_Flow, MM_CIP_Agitator_Speed,MM_CIP_Recir_Speed,MM_CIP_Homo_Speed) select [Date] ,[Time] ,Batch_No,MM_CIP_Recipe_Step ,MM_CIP_Temp, MM_CIP_Flow,MM_CIP_Agitator_Speed,MM_CIP_Recir_Speed,MM_CIP_Homo_Speed FROM SQL_CIP_MM_30S WHERE NOT MM_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_MM ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '101' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_MM ORDER BY [Date] ASC ,[Time] ASC")
    elif db == "PM_CIP_Report":
        st = "SQL_CIP_PM_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_PM")
        Validation_CIP.execute("INSERT Into User_PM ([Date] ,[Time] ,Batch_No,PM_CIP_Recipe_Step ,PM_CIP_Temp,PM_CIP_Flow, PM_CIP_Agitator_Speed,PM_CIP_Recir_Speed,PM_CIP_Homo_Speed) select [Date] ,[Time] ,Batch_No,PM_CIP_Recipe_Step ,PM_CIP_Temp, PM_CIP_Flow,PM_CIP_Agitator_Speed,PM_CIP_Recir_Speed,PM_CIP_Homo_Speed FROM SQL_CIP_PM_30S WHERE NOT PM_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_PM ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '102' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_PM ORDER BY [Date] ASC ,[Time] ASC")
    
    elif db == "ST_CIP_Report":
        st = "SQL_CIP_ST_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_ST")
        Validation_CIP.execute("INSERT Into User_ST ([Date] ,[Time] ,Batch_No,ST_CIP_Recipe_Step ,ST_CIP_Temp,ST_CIP_Flow, ST_CIP_Pump_Speed) select [Date] ,[Time] ,Batch_No,ST_CIP_Recipe_Step ,ST_CIP_Temp, ST_CIP_Flow,ST_CIP_Pump_Speed FROM SQL_CIP_ST_30S WHERE NOT ST_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_ST ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '100' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_ST ORDER BY [Date] ASC ,[Time] ASC")
    
    else :
        st = db
    
     
       #for i in cursor:
    #    print(i)
    return render_template('Validation_CIP.html',data=Validation_CIP,nameUser=nameUser,name=name,db=db,id=id,st=st)
    

@app.route('/Pre_bacth/<string:name1>/<string:name2>', methods=['GET', 'POST'])
@flask_login.login_required
def Pre_bacth(name1,name2):
   
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Pre_bacth  = cnxn.cursor()
    Pre_bacth.execute("SELECT * FROM Pre_Batch_Report  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name1+"' ORDER BY Recipe_Step ASC ")
    #for i in cursor:
    #    print(i)
    
    return render_template('Pre_bacth.html',bacth=name1,id = name2,Pre_bacth=Pre_bacth,nameUser=nameUser)


@app.route('/Main_bacth/<string:name1>/<string:name2>', methods=['GET', 'POST'])
@flask_login.login_required
def Main_bacth(name1,name2):
    
   
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Main_bacth  = cnxn.cursor()
    Main_bacth.execute("""
                        SELECT DISTINCT  Phase_Instance_ID , Phase_ID , UnitOrConnection  ,[DateTime] FROM BatchHistory.dbo.ProcessVar pv WHERE Batch_Log_ID =? AND UnitOrConnection = 'MX101' ORDER BY [DateTime] ASC;
                       """,(name2,))
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+ server +';DATABASE='+database+';UID='+username+';PWD='+password)
    Phase_Parameter = cnxn.cursor()
    Phase_Parameter.execute("SELECT * FROM  BatchHistory.dbo.[Parameter] WHERE MX = 'MX101'") 
    
    Phase_Parameter_DIR = Phase_Parameter.fetchall()

    insertObject = []
    columnNames = [column[0] for column in Phase_Parameter.description]
    for record in Phase_Parameter_DIR:
        insertObject.append( dict( zip( columnNames , record ) ) )
    print(insertObject)
    print(insertObject[0]['ParameterName'])
    return  render_template('Main_bacth.html',Phase_Parameter=insertObject,len=len(Phase_Parameter_DIR),bacth=name1,id = name2,Main_bacth=Main_bacth,nameUser=nameUser)


@app.route('/pdfOverview/<string:name1>/<string:name2>', methods=['GET', 'POST'])
def pdfOverview(name1,name2):

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Main_bacth  = cnxn.cursor()
    Main_bacth.execute("SELECT * FROM Main_Batch_Report  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name1+"' ORDER BY Recipe_Step ASC ")
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Pre_bacth  = cnxn.cursor()
    Pre_bacth.execute("SELECT * FROM Pre_Batch_Report  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name1+"' ORDER BY Recipe_Step ASC ")
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    overview = cnxn.cursor()
    overview.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM Pre_Batch_Report WHERE End_Time LIKE '%:%' AND Batch_No = '"+name1+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC")
   



    rendered = render_template('PdfOverview.html',bacth=name1,id = name2,Main_bacth = Main_bacth,Pre_bacth= Pre_bacth,st = overview)
   
    css = 'testcss.css'
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    #options = {'enable-local-file-access': None,'page-size':'A4', 'orientation': 'landscape','footer-right': 'Page [page]','dpi': 96}
    options = {
            
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.5in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'footer-right': 'Page [page]',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            
            
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options , css=css)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;filename=output.pdf'
    
    return  response

@app.route('/pdfOverview_CIP/<string:name>/<string:db>/<string:id>', methods=['GET', 'POST'])
def pdfOverview_CIP(name,db,id):

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    bacth_CIP  = cnxn.cursor()
    bacth_CIP.execute("SELECT * FROM " + db +"  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name +"' ORDER BY Recipe_Step ASC ")
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    overview_CIP = cnxn.cursor()
    overview_CIP.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM "+db+" WHERE End_Time LIKE '%:%' AND Batch_No ='"+name+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")

   
    rendered = render_template('PdfOverview_CIP.html',data=bacth_CIP,nameUser=nameUser,name=name,db=db,id=id,st=overview_CIP)
   
    css = 'testcss.css'
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    #options = {'enable-local-file-access': None,'page-size':'A4', 'orientation': 'landscape','footer-right': 'Page [page]','dpi': 96}
    options = {
            
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.5in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'footer-right': 'Page [page]',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            
            
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options , css=css)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;filename=output.pdf'
    
    return  response

    
@app.route('/pdfValidation_CIP/<string:name>/<string:db>/<string:id>', methods=['GET', 'POST'])
def pdfValidation_CIP(name,db,id):

    if db == "MM_CIP_Report":
        st = "SQL_CIP_MM_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_MM")
        Validation_CIP.execute("INSERT Into User_MM ([Date] ,[Time] ,Batch_No,MM_CIP_Recipe_Step ,MM_CIP_Temp,MM_CIP_Flow, MM_CIP_Agitator_Speed,MM_CIP_Recir_Speed,MM_CIP_Homo_Speed) select [Date] ,[Time] ,Batch_No,MM_CIP_Recipe_Step ,MM_CIP_Temp, MM_CIP_Flow,MM_CIP_Agitator_Speed,MM_CIP_Recir_Speed,MM_CIP_Homo_Speed FROM SQL_CIP_MM_30S WHERE NOT MM_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_MM ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '101' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_MM ORDER BY [Date] ASC ,[Time] ASC")
    elif db == "PM_CIP_Report":
        st = "SQL_CIP_PM_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_PM")
        Validation_CIP.execute("INSERT Into User_PM ([Date] ,[Time] ,Batch_No,PM_CIP_Recipe_Step ,PM_CIP_Temp,PM_CIP_Flow, PM_CIP_Agitator_Speed,PM_CIP_Recir_Speed,PM_CIP_Homo_Speed) select [Date] ,[Time] ,Batch_No,PM_CIP_Recipe_Step ,PM_CIP_Temp, PM_CIP_Flow,PM_CIP_Agitator_Speed,PM_CIP_Recir_Speed,PM_CIP_Homo_Speed FROM SQL_CIP_PM_30S WHERE NOT PM_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_PM ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '102' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_PM ORDER BY [Date] ASC ,[Time] ASC")
    
    elif db == "ST_CIP_Report":
        st = "SQL_CIP_ST_30S"
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
        Validation_CIP  = cnxn.cursor()
        Validation_CIP.execute("DELETE FROM User_ST")
        Validation_CIP.execute("INSERT Into User_ST ([Date] ,[Time] ,Batch_No,ST_CIP_Recipe_Step ,ST_CIP_Temp,ST_CIP_Flow, ST_CIP_Pump_Speed) select [Date] ,[Time] ,Batch_No,ST_CIP_Recipe_Step ,ST_CIP_Temp, ST_CIP_Flow,ST_CIP_Pump_Speed FROM SQL_CIP_ST_30S WHERE NOT ST_CIP_Recipe_Step = 0  AND Batch_No = '" +name +"' ORDER BY [Date] ASC ,[Time] ASC ")
        Validation_CIP.execute("INSERT Into User_ST ([Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity ,Old_Value,New_Value,Batch_No,Station FROM Adjustments WHERE Batch_No ='" +name +"' AND Station = '100' ORDER BY [Date] ASC ,[Time] ASC")
        Validation_CIP.execute("SELECT * FROM User_ST ORDER BY [Date] ASC ,[Time] ASC")
    
    else :
        st = db

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    bacth_CIP  = cnxn.cursor()
    bacth_CIP.execute("SELECT * FROM " + db +"  WHERE Step_End_Time LIKE '%:%' AND Batch_No = '"+ name +"' ORDER BY Recipe_Step ASC ")
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    overview_CIP = cnxn.cursor()
    overview_CIP.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM "+db+" WHERE End_Time LIKE '%:%' AND Batch_No ='"+name+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")

   
    print(Main_Validation)
    print(Main_Validation)
    rendered = render_template('pdfValidation_CIP.html',bacth=name,id = id,data=Validation_CIP,nameUser=nameUser,st = overview_CIP,db=st)
   

    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    #options = {'enable-local-file-access': None,'page-size':'A4', 'orientation': 'landscape','footer-right': 'Page [page]','dpi': 96}
    options = {
            
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.5in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'footer-right': 'Page [page]',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            
            
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;filename=output.pdf'
    
    return  response

@app.route('/pdfMain_val/<string:name1>/<string:name2>', methods=['GET', 'POST'])
def pdfMain_val(name1,name2):

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Main_Validation  = cnxn.cursor()
    Main_Validation.execute("DELETE FROM User_Main")
    Main_Validation.execute("INSERT Into User_Main ([Date] ,[Time] ,MM_Recipe_Step ,MM_Weight,MM_Temp, MM_Recir_Temp,MM_Pressure,Agitator_Speed,Recir_Speed,Homo_Speed,Recir_Status,Recir_Homo_Mode ,Recir_Cool_Mode) SELECT [Date] ,[Time] ,MM_Recipe_Step ,MM_Weight,MM_Temp ,MM_Recir_Temp,MM_Pressure,Agitator_Speed,Recir_Speed,Homo_Speed,Recir_Status,Recir_Homo_Mode ,Recir_Cool_Mode FROM Main_Mixer WHERE NOT MM_Recipe_Step = 0  AND Batch_No = '" + name1+"' ORDER BY [Date] ASC ,[Time] ASC ")
    Main_Validation.execute("INSERT Into User_Main ([Date] ,[Time],User_Name,User_Level,User_Activity ,User_Old_Value,User_New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity,Old_Value,New_Value,Batch_No,Station FROM User_Adjust WHERE Batch_No = '" + name1+"' AND Station = '101' ORDER BY [Date] ASC ,[Time] ASC")
    Main_Validation.execute("SELECT * FROM User_Main ORDER BY [Date] ASC ,[Time] ASC")

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    overview = cnxn.cursor()
    overview.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM Pre_Batch_Report WHERE End_Time LIKE '%:%' AND Batch_No = '"+name1+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC")
   
   
    print(Main_Validation)
    print(Main_Validation)
    rendered = render_template('PdfMain_val.html',bacth=name1,id = name2,Main_Validation=Main_Validation,nameUser=nameUser,st = overview)
   

    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    #options = {'enable-local-file-access': None,'page-size':'A4', 'orientation': 'landscape','footer-right': 'Page [page]','dpi': 96}
    options = {
            
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.5in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'footer-right': 'Page [page]',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            
            
    }
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;filename=output.pdf'
    
    return  response
    
@app.route('/pdfPre_val/<string:name1>/<string:name2>', methods=['GET', 'POST'])
def pdfPre_val(name1,name2):

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Pre_Validation  = cnxn.cursor()
    Pre_Validation.execute("DELETE FROM User_Pre")
    Pre_Validation.execute("INSERT Into User_Pre ([Date] ,[Time],PM_Recipe_Step ,PM_Weight ,PM_Temp ,Agitator_Speed ) SELECT [Date] ,[Time],PM_Recipe_Step ,PM_Weight ,PM_Temp ,Agitator_Speed FROM Pre_Mixer WHERE NOT PM_Recipe_Step = 0  AND Batch_No = '" + name1+"' ORDER BY [Date] ASC ,[Time] ASC ")
    Pre_Validation.execute("INSERT Into User_Pre ([Date] ,[Time],User_Name,User_Level,User_Activity ,User_Old_Value,User_New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity,Old_Value,New_Value,Batch_No,Station FROM User_Adjust WHERE Batch_No = '" + name1+"' AND Station = '102' ORDER BY [Date] ASC ,[Time] ASC")
    Pre_Validation.execute("SELECT * FROM User_Pre ORDER BY [Date] ASC ,[Time] ASC")

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    overview = cnxn.cursor()
    overview.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM Pre_Batch_Report WHERE End_Time LIKE '%:%' AND Batch_No = '"+name1+"' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC")
   
    
     
    print(Pre_Validation)
    print(Pre_Validation)
    rendered = render_template('PdfPre_val.html',bacth=name1,id = name2,Pre_Validation=Pre_Validation,nameUser=nameUser,st = overview)
   

    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    #options = {'enable-local-file-access': None,'page-size':'A4', 'orientation': 'landscape','footer-right': 'Page [page]','dpi': 96}
    options = {
            
            'page-size': 'A4',
            'orientation': 'landscape',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.5in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'footer-right': 'Page [page]',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            
            
    }

    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline;filename=output.pdf'
    
    return  response
    

@app.route('/Main_Validation/<string:name1>/<string:name2>', methods=['GET', 'POST'])
@flask_login.login_required
def Main_Validation(name1,name2):
   
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Main_Validation  = cnxn.cursor()
    Main_Validation.execute("DELETE FROM User_Main")
    Main_Validation.execute("INSERT Into User_Main ([Date] ,[Time] ,MM_Recipe_Step ,MM_Weight,MM_Temp, MM_Recir_Temp,MM_Pressure,Agitator_Speed,Recir_Speed,Homo_Speed,Recir_Status,Recir_Homo_Mode ,Recir_Cool_Mode) SELECT [Date] ,[Time] ,MM_Recipe_Step ,MM_Weight,MM_Temp ,MM_Recir_Temp,MM_Pressure,Agitator_Speed,Recir_Speed,Homo_Speed,Recir_Status,Recir_Homo_Mode ,Recir_Cool_Mode FROM Main_Mixer WHERE NOT MM_Recipe_Step = 0  AND Batch_No = '" + name1+"' ORDER BY [Date] ASC ,[Time] ASC ")
    Main_Validation.execute("INSERT Into User_Main ([Date] ,[Time],User_Name,User_Level,User_Activity ,User_Old_Value,User_New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity,Old_Value,New_Value,Batch_No,Station FROM User_Adjust WHERE Batch_No = '" + name1+"' AND Station = '101' ORDER BY [Date] ASC ,[Time] ASC")
    Main_Validation.execute("SELECT * FROM User_Main ORDER BY [Date] ASC ,[Time] ASC")
        #for i in cursor:
    print(Main_Validation)
    return render_template('Main_Validation.html',Validation=name1,id = name2,Main_Validation=Main_Validation,nameUser=nameUser)



@app.route('/Pre_Validation/<string:name1>/<string:name2>', methods=['GET', 'POST'])
@flask_login.login_required
def Pre_Validation(name1,name2):
   
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    Pre_Validation  = cnxn.cursor()
    Pre_Validation.execute("DELETE FROM User_Pre")
    Pre_Validation.execute("INSERT Into User_Pre ([Date] ,[Time],PM_Recipe_Step ,PM_Weight ,PM_Temp ,Agitator_Speed ) SELECT [Date] ,[Time],PM_Recipe_Step ,PM_Weight ,PM_Temp ,Agitator_Speed FROM Pre_Mixer WHERE NOT PM_Recipe_Step = 0  AND Batch_No = '" + name1+"' ORDER BY [Date] ASC ,[Time] ASC ")
    Pre_Validation.execute("INSERT Into User_Pre ([Date] ,[Time],User_Name,User_Level,User_Activity ,User_Old_Value,User_New_Value,Batch_No,Station) SELECT [Date] ,[Time],User_Name,User_Level,Activity,Old_Value,New_Value,Batch_No,Station FROM User_Adjust WHERE Batch_No = '" + name1+"' AND Station = '102' ORDER BY [Date] ASC ,[Time] ASC")
    Pre_Validation.execute("SELECT * FROM User_Pre ORDER BY [Date] ASC ,[Time] ASC")
    #for i in cursor:
    #    print(i)
    return render_template('Pre_Validation.html',Validation=name1,id = name2,Pre_Validation=Pre_Validation,nameUser=nameUser)
    

@app.route('/home', methods=['GET', 'POST'])
@flask_login.login_required
def home():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()
    cursor.execute("""
                   SELECT bil.Batch_Log_ID , bil.Campaign_ID,bil.Lot_ID,bil.Batch_ID,bil.Product_ID,bil.Product_Name,bil.Recipe_ID,bil.Recipe_Name,bil.Batch_Size,MIN(pv.[DateTime]) as StartDateTime , MAX(pv.[datetime]) as StopDateTime
                    FROM  BatchHistory.dbo.BatchIdLog bil 
                    inner join BatchHistory.dbo.ProcessVar pv 
                    ON bil.Batch_Log_ID = pv.Batch_Log_ID 
                    GROUP BY bil.Batch_Log_ID , bil.Campaign_ID,bil.Lot_ID,bil.Batch_ID,bil.Product_ID,bil.Product_Name,bil.Recipe_ID,bil.Recipe_Name,bil.Batch_Size
                    ORDER BY MIN(pv.[DateTime]) DESC
                    """)
    # for i in cursor:
    #    print(i)
    return render_template('home.html',data = cursor,nameUser=nameUser)  


@app.route('/home_CIP_Mix', methods=['GET', 'POST'])
@flask_login.login_required
def home_CIP_Mix():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    cursor = cnxn.cursor()
    cursor.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM MM_CIP_Report WHERE End_Time LIKE '%:%' AND NOT Batch_No ='' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")
    # for i in cursor:
    #    print(i)
    mode = 'Main Mixier'
    db = 'MM_CIP_Report'

    return render_template('home_CIP.html',mode = mode,db=db,data = cursor,nameUser=nameUser)  

@app.route('/home_CIP_Pre', methods=['GET', 'POST'])
@flask_login.login_required
def home_CIP_Pre():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    cursor = cnxn.cursor()
    cursor.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM PM_CIP_Report WHERE End_Time LIKE '%:%' AND NOT Batch_No ='' GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")
    # for i in cursor:
    #    print(i)
    mode = 'Pre Mixier'
    db = 'PM_CIP_Report'
    return render_template('home_CIP.html',mode = mode,db=db,data = cursor,nameUser=nameUser)  

@app.route('/home_CIP_ST100', methods=['GET', 'POST'])
@flask_login.login_required
def home_CIP_ST100():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    cursor = cnxn.cursor()
    cursor.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM ST_CIP_Report WHERE End_Time LIKE '%:%' AND NOT Batch_No ='' AND Parameter_21_SP = 100 GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")
    # for i in cursor:
    #    print(i)
    mode = 'Storage Tank 100'
    db = 'ST_CIP_Report'
    return render_template('home_CIP.html',mode = mode,db=db,data = cursor,nameUser=nameUser)  

@app.route('/home_CIP_ST200', methods=['GET', 'POST'])
@flask_login.login_required
def home_CIP_ST200():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-4PSV1LF;DATABASE=RB_2T_CIP;UID=sa;PWD=12345678')
    cursor = cnxn.cursor()
    cursor.execute("SELECT DISTINCT Batch_No, MAX(Recipe_Name),MAX(Start_Date),MAX(Start_Time),MAX(End_Date),MAX(End_Time),MAX(timeSt) FROM ST_CIP_Report WHERE End_Time LIKE '%:%' AND NOT Batch_No ='' AND Parameter_21_SP = 200 GROUP BY Batch_No ORDER BY MAX(timeSt) DESC ")
    # for i in cursor:
    #    print(i)
    mode = 'Storage Tank 200'
    db = 'ST_CIP_Report'
    return render_template('home_CIP.html',mode = mode,db=db,data = cursor,nameUser=nameUser)  


@app.route('/User_Management', methods=['GET', 'POST'])
@flask_login.login_required
def User_Management():
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    User_Management = cnxn.cursor()
    User_Management.execute("SELECT  * FROM Login ORDER BY id ASC ")
    
    # for i in cursor:
    #    print(i)
    return render_template('User_Management.html',nameUser=nameUser,User_Management=User_Management)
    

@app.route('/delete/<string:name>', methods=['GET'])
@flask_login.login_required
def delete(name):
    
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    delete = cnxn.cursor()
    delete.execute("DELETE FROM Login WHERE id = " + name )
    delete.commit()
    print(name)
    # for i in cursor:
    #    print(i)
    return redirect(url_for('User_Management'))

@app.route('/update', methods=["GET", "POST"])
@flask_login.login_required
def update():

    if request.method == "POST":
        user = request.form['username']
        password = request.form['password']
        id = request.form['id']
        print(user)
        print(password)
        print(id)

    
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        update = cnxn.cursor()
        update.execute("UPDATE Login SET username = '"+ user+ "' ,password = '"+ password +"' WHERE id = " + id)
        update.commit()
        return redirect(url_for('User_Management'))
    
    # for i in cursor:
    #    print(i)
    return redirect(url_for('User_Management'))

@app.route('/add', methods=["GET", "POST"])
@flask_login.login_required
def add():

    if request.method == "POST":
        user = request.form['username']
        password = request.form['password']
        print(user)
        print(password)

        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        add = cnxn.cursor()
        try:
            add.execute("INSERT INTO Login (username ,password) VALUES ('" + user + "', '" + password + "')")
            add.commit()
            return redirect(url_for('User_Management'))
        except:

            return "<link href='{{ url_for('static', filename='bootstrap/dist/css/bootstrap.min.css') }}' rel='stylesheet'> <br> <h1 style='text-align: center'> คุณใส่ชื่อ User ซ้ำ กรุณาลองใหม่อีกครั้ง. <h1> <br> <a href='/User_Management' class'btn btn-secondary'>Back</a>"
    
    # for i in cursor:
    #    print(i)
    return redirect(url_for('User_Management'))
     

if __name__ == "__main__": 
    app.run(host='0.0.0.0', debug=True, port=5000)
    