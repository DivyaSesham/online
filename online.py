from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_mysqldb import MySQL
from flask_session import Session
from otp import genotp
from cmail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO                      # files input &output package
app=Flask(__name__)
app.secret_key='*grsig@khgy'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='user'
Session(app)
mysql=MySQL(app)
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/userreg',methods=['GET','POST'])
def userreg():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        mobile=request.form['mobile']
        gender=request.form['gender']
        
        
        cursor=mysql.connection.cursor()
        cursor.execute('Select username from userinfo')
        data=cursor.fetchall()
        cursor.execute('SELECT email from userinfo')
        edata=cursor.fetchall()
        if(username,)in data:
            flash('User already already exists')
            return render_template('userreg.html')
        if(email,) in edata:
            flash('Email id  already already exists')
            return render_template('userreg.html')
        cursor.close()
        otp=genotp()
        subject='Thanks for registering to the application'
        body=f'Use this otp to register {otp}'
        sendmail(email,body,subject)
        return render_template('otp.html',otp=otp,username=username,password=password,email=email,mobile=mobile,gender=gender)
    return render_template('userreg.html')
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if session.get('user'):
        return redirect(url_for('studentbase'))
    
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from userinfo where username=%s and password=%s',[username,password])
        count=cursor.fetchone()  [0]
        if count==0:
            flash('Invalid username or password')
            return render_template('userlogin.html')
        else:
            session['studentid']=username
            return redirect(url_for('studentbase'))
    return render_template('userlogin.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash('already logged out!')
        return redirect(url_for('userlogin'))
@app.route('/otp/<otp>/<username>/<password>/<email>/<mobile>/<gender>',methods=['GET','POST'])
def otp(otp,username,password,email,mobile,gender):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            lst=[username,password,email,mobile,gender]
            query='insert into userinfo values(%s,%s,%s,%s,%s)'
            cursor=mysql.connection.cursor()
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('userlogin'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,username=username,password=password,email=email,mobile=mobile,gender=gender)
@app.route('/forgetpassword',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        username=request.form['username']
        cursor=mysql.connection.cursor()
        cursor.execute('select username from userinfo')
        data=cursor.fetchall()
        if  (username,) in data:
            cursor.execute('select email from userinfo where username=%s',[username])
            data=cursor.fetchone() [0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("createpassword",token=token(username,240))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('userlogin'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')

@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        username=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update userinfo set password=%s where username=%s',[npass,username])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'
 
@app.route('/aindex')
def aindex():
    return render_template('aindex.html')

@app.route('/adminreg',methods=['GET','POST'])
def adminreg():
    if request.method=='POST':
        name=request.form['username']
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        # check if the email already exists
        cursor.execute('SELECT COUNT(*) FROM admin WHERE email = %s', [email])
        count = cursor.fetchone()[0]
        if count > 0:
            flash('Email id already exists')
            return render_template('adminreg.html')
        # check if the passcode matches
        else:
            cursor.execute('INSERT INTO admin VALUES (%s,%s,%s)',[name,email,password])
            mysql.connection.commit()
            cursor.close()
            flash("Admin account created successfully")
            return redirect(url_for('adminlogin'))
    return render_template('adminreg.html')
    
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if session.get('user'):
        return redirect(url_for('admin'))
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from admin where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid username or password')
            return render_template('adminlogin.html')
        else:
            session['user']=username
            return redirect(url_for('admin'))
    return render_template('adminlogin.html')

@app.route('/adminforgotpassword',methods=['GET','POST'])
def adminforgot():
    if request.method=='POST':
        username=request.form['username']
        cursor=mysql.connection.cursor()
        cursor.execute('select username from admin')
        data=cursor.fetchall()
        print (data)
        if  (username,) in data:
            cursor.execute('select email from admin where username=%s',[username])
            data=cursor.fetchone() [0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("adminpassword",token=token(username,240))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('adminlogin'))
        else:
            return 'Invalid user id'
    return render_template('adminforgot.html')

@app.route('/adminpassword/<token>',methods=['GET','POST'])
def adminpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        username=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where username=%s',[npass,username])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('adminnewpassword.html')
    except: 
        return 'Link expired try again'

@app.route('/admin')
def admin():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT COUNT(*) from userinfo')
    sdata=cursor.fetchone()[0]
    cursor.execute('select count(*) from course')
    cdata=cursor.fetchone()[0]
    return render_template('admin.html',sdata=sdata,cdata=cdata)
    
@app.route('/admincourse')
def admincourse():
    return render_template('admincourse.html')
@app.route('/adminques')
def adminques():
    return render_template('adminques.html')


@app.route('/addcourse',methods=['GET','POST'])
def addcourse():
    if session.get('user'):
        if request.method=='POST':
           courseid=request.form['id']
           coursename=request.form['cname']
           duration=request.form['duration']
          
           cursor=mysql.connection.cursor()
           cursor.execute('insert into course(course_id,course_name,duration)values(%s,%s,%s)',[courseid,coursename,duration])
           mysql.connection.commit()
           cursor.close()
           flash('Details Registered')
           return redirect(url_for('admincourse'))
        return render_template('addcourse.html')
    else:
       
        return redirect(url_for('addcourse'))
@app.route('/viewcourse')
def viewcourse():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from course')
        course_data=cursor.fetchall()
        print(course_data)
        cursor.close()
        return render_template('viewcourse.html',data=course_data)     

    else:
        return redirect(url_for('login'))
@app.route('/delete/<course_id>')
def delete(course_id):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from course where course_id=%s',[course_id])
    mysql.connection.commit()
    cursor.close()
    flash('Course deleted successfully')
    return redirect(url_for('viewcourse'))
@app.route('/addquestions',methods=['GET','POST'])
def addquestions():
    cursor=mysql.connection.cursor()
    cursor.execute('select course_id from course')
    data=cursor.fetchall()
    if session.get('user'):
        if request.method=='POST':
            cursor=mysql.connection.cursor()
            q_id=request.form['id']
            q_name=request.form['name']
            course_id=request.form['one']
            option1=request.form['option1']
            option2=request.form['option2']
            option3=request.form['option3']
            option4=request.form['option4']
            correct_option=request.form['coption']
            marks=request.form['marks']
            cursor=mysql.connection.cursor()
            cursor.execute('insert into question(q_id,q_name,course_id,option1,option2,option3,option4,correct_option,marks)values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[q_id,q_name,course_id,option1,option2,option3,option4,correct_option,marks])
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('adminques'))
        return render_template('addquestions.html',data=data)
    else:
       
        return redirect(url_for('addquestions'))
@app.route('/allquestions')
def allquestions():
    if session.get('user'):

        cursor=mysql.connection.cursor()
        cursor.execute('select * from question')
        question_data=cursor.fetchall()
        
        cursor.close()
        return render_template('allquestions.html',data=question_data)     
    else:
        return redirect(url_for('login'))

@app.route('/update/<q_id>',methods=['GET','POST'])
def update(q_id):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select q_id,q_name,course_id,option1,option2,option3,option4,correct_option,marks from question where q_id=%s',[q_id])
        q_data=cursor.fetchone()
        print(q_data)
        cursor=mysql.connection.cursor()
        cursor.execute('select course_id from course')
        data=cursor.fetchall()
        
        
        cursor.close()
        if request.method=='POST':
            q_id=request.form['q_id']
            q_name=request.form['q_name']
            course_id=request.form['one']
            option1=request.form['option1']
            option2=request.form['option2'] 
            option3=request.form['option3']
            option4=request.form['option4']
            correct_option=request.form['correct_option']
            marks=request.form['marks']
            cursor=mysql.connection.cursor()
            cursor.execute('update question set q_id=%s,q_name=%s,course_id=%s,option1=%s,option2=%s,option3=%s,option4=%s,correct_option=%s,marks=%s where q_id=%s',[q_id,q_name,course_id,option1,option2,option3,option4,correct_option,marks,q_id])
            mysql.connection.commit()
            cursor.close()
            flash('Questions updated successfully')
            return redirect(url_for('addquestions'))
        return render_template('update.html',data=data,q_data=q_data)
    else:
        return redirect(url_for('login'))

@app.route('/studentbase')
def studentbase():
    user=session['studentid']
    return render_template('studentbase.html')
@app.route('/studentdashboard')
def studentdashboard():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT count(*) from course')
    data=cursor.fetchone()[0]
    #total_courses=a[0]
    cursor.close()
    return render_template('studentdashboard.html',data=data)
@app.route('/coursedetails')
def studentcoursedetails():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from course')
    courselist=cursor.fetchall()    
    cursor.close()
    return render_template('studentcoursedetails.html',courselist=courselist)
@app.route('/studentexam')
def studentexam():
    cursor=mysql.connection.cursor()   
    cursor.execute('SELECT course_name from course')
    data=cursor.fetchall()
    #data1=data[0]
    #print(data)
    #print(a)
    cursor.close()
    return render_template('studentexam.html',course_name=data)
@app.route('/examinstructions/<course_name>')
def takeexam(course_name):
    return render_template('takeexam.html',course_name=course_name)
@app.route('/attempts/<course_name>')
def attempt(course_name):
    students=session['studentid']
    cursor=mysql.connection.cursor()
    cursor.execute('select course_id from course where course_name=%s',[course_name]);
    course_id=cursor.fetchone()[0]
    cursor.execute('select count(*) from submit where username=%s and course_id=%s',[students,course_id])
    result=int(cursor.fetchone()[0])
    if result>0:
        return render_template('noattempt.html')
    else:
        return redirect(url_for('takeexam',course_name=course_name))
@app.route('/submission')
def submit():
    return render_template('examsubmit.html')
@app.route('/startexam/<course_name>',methods=['GET','POST'])
def startexam(course_name):
    cursor=mysql.connection.cursor()
    cursor.execute('select course_id from course where course_name=%s',[course_name]);
    course_id=cursor.fetchone()[0]
    cursor.execute('SELECT q_id,q_name,course_id,option1,option2,option3,option4,correct_option,marks from question where course_id=%s',[course_id])
    data=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        selectedoption=request.form.getlist('options')
        print(selectedoption)
        students=session['studentid']
        course_id=course_id
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT q_id from question where course_id=%s',[course_id])
        question_id=cursor.fetchall()
        #print(course_id)
        #print( question_id)
        for i,j in zip(selectedoption,question_id):
                cursor=mysql.connection.cursor()
                cursor.execute('insert into submit (optionselected,username,course_id,q_id) values(%s,%s,%s,%s)',[i,students,course_id,j])
                mysql.connection.commit()
                cursor.close()
        return redirect(url_for('submit'))
    
    #print(a)
    #print(data)                        
    return render_template('startexam.html',data=data,course_id=course_id)
@app.route('/studentmarks')
def studentmarks():
    students=session['studentid']
    #print(students)
    cursor=mysql.connection.cursor()
    cursor.execute('select distinct(course_id) from submit where username=%s',[students]);
    courseid=cursor.fetchall()
    #print(courseid)
    cursor.close()
    return render_template('studentmarks.html',courseid=courseid)    
@app.route('/checkmarks/<course_id>',methods=['GET'])
def checkmarks(course_id):
    students=session['studentid']
    #print(students)
    cursor=mysql.connection.cursor()
    cursor.execute('select distinct(q_id) from submit where course_id=%s',[course_id])
    question_id=cursor.fetchall()
    cursor.execute('select count(q_id) from question where course_id=%s',[course_id])
    data=cursor.fetchone()[0]
    cursor.execute('select sum(marks) from question where course_id=%s',[course_id])
    data1=cursor.fetchone()[0]
    #print(question_id)
    cursor.execute('select optionselected from submit where username=%s and course_id=%s',[students,course_id])
    selectedoption=cursor.fetchall()
    #print(selectedoption)
    cursor.execute('select correct_option  from question where course_id=%s',[course_id])
    correctoption=cursor.fetchall()
    print(correctoption)
    cursor.execute('select marks from question where course_id=%s',[course_id])
    marks=cursor.fetchall()
    #print(correctoption)    
    for i in question_id:        
        count=0
        for l,m,n in zip(correctoption,selectedoption,marks):
            if l==m:
                count+=int(n[0])
            else:
                count+=0            
    cursor.close()
    return render_template('checkmarks.html',count=count,course_id=course_id,data=data,data1=data1)
@app.route('/alogout')
def alogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('adminlogin'))
    else:
        flash('session already poped')
        return redirect(url_for('adminlogin'))
app.run(use_reloader=True,debug=True)


