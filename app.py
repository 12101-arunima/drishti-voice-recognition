from flask import Flask, redirect, render_template, url_for, request, flash, session
from flaskext.mysql import MySQL
from werkzeug.utils import secure_filename
import os
import json
import pyttsx3
import speech_recognition as sr
from datetime import date
import _thread
from flask_mail import Mail, Message

app = Flask(__name__)

app.secret_key = 'drishti'

mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'drishti_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_DEFAULT_SENDER'] = 'arunimasanthosh2021@mca.ajce.in"'
app.config['MAIL_USERNAME'] = 'arunimasanthosh2021@mca.ajce.in"'
app.config['MAIL_PASSWORD'] = 'Arunima1997##'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


def getData(sql, vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0:
        cur.execute(sql)
    else:
        cur.execute(sql, vals)
    res = cur.fetchall()
    cur.close()
    con.close()
    return res


def setData(sql, vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0:
        cur.execute(sql)
    else:
        cur.execute(sql, vals)
    con.commit()
    cur.close()
    con.close()
    res = cur.rowcount
    return res


def speak(*txt):
    eng = pyttsx3.init()
    voices = eng.getProperty('voices')
    eng.setProperty('voice', voices[1].id)
    eng.setProperty('rate', 125)
    for t in txt:
        eng.say(t)
    eng.runAndWait()
    eng.stop


def listenVoice():
    rec = sr.Recognizer()
    try:
        with sr.Microphone() as src:
            rec.adjust_for_ambient_noise(src, duration=0.2)
            aud = rec.listen(src)
            txt = rec.recognize_google(aud)
            txt = txt.lower()
            return txt
    except sr.RequestError as e:
        # speak('Please check your internet connection')
        return '-2'

    except sr.UnknownValueError:
        # speak('cannot recognize the speek. Please say again')
        return '-1'


@app.route('/getSubject', methods=['POST', 'GET'])
def getSubject():
    cid = request.form['cid']
    sql = "select * from subjects where cid=%s" % cid
    res = getData(sql)
    return json.dumps(res)


@app.route('/listen/', methods=['POST'])
def listenTxt():
    return listenVoice()


@app.route('/getExamDuration/', methods=['POST'])
def examDuration():
    eid = request.form['eid']
    sql = "select duration from exams where eid=%s" % eid
    dur = getData(sql)[0][0]
    return str(dur)


@app.route('/getQuestion/', methods=['POST'])
def getExamQuestion():
    data = request.form
    sql = "select qid,question,opt1,opt2,opt3,opt4,answer from questions where eid=%s order by qid asc limit %s,1"
    vals = (data['eid'], int(data['cnt'])-1)
    res = getData(sql, vals)
    # txt = ('Question number %s' % data['cnt'],res[0][1],'option a',res[0][2],'option b',res[0][3],'option c',res[0][4],'option d',res[0][5])
    # _thread.start_new_thread(speak,txt)
    return json.dumps(res)


@app.route('/user/exam/setresult/', methods=['POST'])
def setExamResult():
    data = request.form
    sql = "select ifnull(max(rid),0)+1 from results"
    rid = getData(sql)[0][0]
    sql = "insert into results values(%s,%s,%s,%s)"
    vals = (rid, data['eid'], session['uid'], data['score'])
    setData(sql, vals)
    return '1'


@app.route('/login/custom/', methods=['POST'])
def customLogin():
    data = request.form
    sql = "select log_id,role from login where username=%s and password=%s"
    vals = (data['uname'], data['pword'])
    res = getData(sql, vals)
    if len(res):
        session['uid'] = res[0][0]
        session['role'] = res[0][1]
    return json.dumps(res)


@app.route('/')
def home():
    if 'uid' in session and 'role' in session:
        return redirect('/'+session['role']+'/home')
    return render_template('public/home.html')


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.form
        sql = "select log_id,role from login where username=%s and password=%s"
        vals = (data['uname'], data['pword'])
        res = getData(sql, vals)
        if len(res):
            session['uid'] = res[0][0]
            session['role'] = res[0][1]
            return redirect('/'+res[0][1]+'/home')
        else:
            flash('Invalid login details')
    return render_template('public/login.html')


@app.route('/admin/addUser', methods=['POST', 'GET'])
def register():
    data = ''
    if request.method == 'POST':
        data = request.form
        if data['pword'] == data['cpword']:
            sql = "select count(*) from login where username='%s'" % data['uname']
            res = getData(sql)
            if res[0][0] == 0:
                sql = "select count(*) from user_details where phone='%s'" % data['phone']
                res = getData(sql)
                if res[0][0] == 0:
                    file = request.files['photo']
                    fn = os.path.basename(file.filename).split('.')
                    fn = fn[len(fn)-1]
                    sql = "select ifnull(max(log_id),0)+1 from login"
                    res = getData(sql)
                    log_id = res[0][0]
                    sql = "insert into login values(%s,%s,%s,'user')"
                    vals = (log_id, data['uname'], data['pword'])
                    setData(sql, vals)
                    fn = "%s.%s" % (log_id, fn)
                    sql = "insert into user_details values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    vals = (log_id, data['fname'], data['lname'], data['address'], data['street'], data['city'], data['state'],
                            data['pin'], data['phone'], data['email'], data['dob'], data['gender'], fn, data['course'])
                    setData(sql, vals)
                    file.save('static/uploads/'+secure_filename(fn))

                  #  _topic = 'Your username is %s and password is %s' % (data['uname'],data['pword'])
                   # _sub = 'Account Registration'
                  #  _from = ''
                  #  _to = [data['email']]
                   # msg = Message(_sub, sender=_from, recipients=_to)
                  #  msg.body = _topic
                  #  mail.send(msg)

                    return redirect(url_for('viewUsers'))
                else:
                    flash('Phone Number Already Exists')
            else:
                flash('Username Already Exists')     
        else:
            flash('Passwords Not Matching')
    sql = "select * from courses"
    res = getData(sql)
    return render_template('admin/register.html', courses=res, data=data)


@app.route('/admin/home')
def adminHome():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select eid,title,date,time,duration,s.name,c.name from exams e join subjects s on s.sid=e.sid join courses c on c.cid=s.cid order by e.date desc"
    res = getData(sql)
    return render_template('admin/home.html', exams=res)


@app.route('/admin/addExam', methods=['POST', 'GET'])
def addExam():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(eid),0)+1 from exams"
        res = getData(sql)
        eid = res[0][0]
        sql = "insert into exams values(%s,%s,%s,%s,%s,%s,1)"
        vals = (eid, data['subject'], data['title'],
                data['date'], data['time'], data['duration'])
        setData(sql, vals)
        return redirect(url_for('adminHome'))
    courses = getData("select * from courses order by name")
    sql = "select * from subjects where cid=%s" % courses[0][0]
    subjects = getData(sql)
    return render_template('admin/addExam.html', courses=courses, subjects=subjects)


@app.route('/admin/viewQuestions/<eid>/', methods=['POST', 'GET'])
def viewQuestion(eid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(qid),0)+1 from questions"
        res = getData(sql)
        qid = res[0][0]
        sql = "insert into questions values(%s,%s,%s,%s,%s,%s,%s,%s)"
        vals = (qid, eid, data['question'], data['opt1'],
                data['opt2'], data['opt3'], data['opt4'], data['answer'])
        setData(sql, vals)
    sql = "select * from questions where eid=%s" % eid
    res = getData(sql)
    sql = "select count(*) from exams where eid=%s and date <= current_date" % eid
    d = getData(sql)
    dt = False
    if d[0][0] == 0:
        dt = True
    return render_template('admin/viewQuestions.html', questions=res, dt=dt)

@app.route('/admin/getIndQuestion/',methods=['POST'])
def getIndQuestion():
    sql = "select question,opt1,opt2,opt3,opt4,answer from questions where qid=%s" % request.form['qid']
    res = getData(sql)
    return json.dumps(res[0])

@app.route('/admin/updateQuestion/',methods=['POST'])
def updateQuestion():
    data = request.form
    sql = "update questions set question=%s,opt1=%s,opt2=%s,opt3=%s,opt4=%s,answer=%s where qid=%s"
    vals = (data['question'],data['opt1'],data['opt2'],data['opt3'],data['opt4'],data['ans'],data['qid'])
    setData(sql,vals)
    return '1'

@app.route('/admin/deleteQuestion/<qid>/<eid>/')
def deleteQuestion(qid, eid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "delete from questions where qid=%s" % qid
    setData(sql)
    return redirect(url_for('viewQuestion', eid=eid))


@app.route('/admin/courses', methods=['POST', 'GET'])
def adminCourse():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        course = request.form['name']
        sql = "select count(*) from courses where name='%s'" % course
        res = getData(sql)
        if res[0][0] == 0:
            sql = "select ifnull(max(cid),0)+1 from courses"
            res = getData(sql)
            cid = res[0][0]
            sql = "insert into courses values(%s,%s)"
            vals = (cid, course)
            setData(sql, vals)
        else:
            flash("Course Already Exists")
    sql = "select * from courses"
    res = getData(sql)
    return render_template('admin/courses.html', courses=res)


@app.route('/admin/viewSubjects/<cid>/', methods=['GET', 'POST'])
def viewSubjects(cid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        subject = request.form['name']
        sql = "select count(*) from subjects where name=%s and cid=%s"
        vals = (subject, cid)
        res = getData(sql, vals)
        if res[0][0] == 0:
            sql = "select ifnull(max(sid),0)+1 from subjects"
            res = getData(sql)
            sid = res[0][0]
            sql = "insert into subjects values(%s,%s,%s)"
            vals = (sid, subject, cid)
            setData(sql, vals)
        else:
            flash("Subject Already Exists")
    sql = "select * from subjects where cid=%s" % cid
    res = getData(sql)
    return render_template('admin/viewSubjects.html', subjects=res)


@app.route('/admin/deleteSubject/<sid>/<cid>/')
def deleteSubject(sid, cid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select count(*) from exams where sid=%s" % sid
    res = getData(sql)
    if res[0][0] == 0:
        sql = "delete from subjects where sid=%s" % sid
        setData(sql)
        flash("Subject Deleted!")
    else:
        flash("Existing Exams Found In This Subject!!")
    return redirect(url_for('viewSubjects', cid=cid))


@app.route('/admin/viewResults/<eid>/')
def adminViewResult(eid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select rid,mark,concat(fname,' ',lname) as name from results r join user_details u on u.uid=r.uid where r.eid=%s" % eid
    res = getData(sql)
    return render_template('admin/viewResult.html', results=res)


@app.route('/admin/viewUsers')
def viewUsers():
    sql = "select uid,concat(fname,' ',lname) as name,c.name,phone from user_details u join courses c on c.cid=u.cid"
    res = getData(sql)
    return render_template('admin/viewUsers.html', users=res)


@app.route('/admin/userDetails/<uid>/')
def viewUserDetails(uid):
    sql = "select uid,concat(fname,' ',lname) as name,concat(address,' ',street,' ',city,' ',state,' ',pin_code),phone,dob,gender,photo,username as email,c.name as course from user_details u join login l on l.log_id=u.uid join courses c on c.cid=u.cid where uid=%s" % uid
    res = getData(sql)
    return render_template('admin/userDetails.html', data=res[0])


@app.route('/admin/viewFeedbacks', methods=['GET', 'POST'])
def viewFeedbacks():
    if request.method == 'POST':
        data = request.form
        sql = "update feedbacks set reply=%s where fid=%s"
        vals = (data['reply'], data['fid'])
        setData(sql, vals)
        flash("Reply Sended")
    sql = "select fid,message,date,reply,concat(fname,' ',lname) as name from feedbacks f join user_details u on u.uid=f.uid"
    res = getData(sql)
    return render_template('admin/viewFeedbacks.html', feedbacks=res)


@app.route('/admin/adminJobs', methods=['POST', 'GET'])
def adminJobs():
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(jid),0)+1 from jobs"
        res = getData(sql)
        jid = res[0][0]
        sql = "insert into jobs values(%s,%s,%s,current_date,%s)"
        vals = (jid, data['title'], data['description'], data['course'])
        setData(sql, vals)
        flash('Job Added')
    sql = "select * from courses"
    res = getData(sql)
    sql = "select jid,title,description,date,name course from jobs j join courses c on c.cid=j.cid order by date"
    res1 = getData(sql)
    return render_template('admin/jobs.html', jobs=res1, courses=res)


@app.route('/admin/deleteJob/<jid>/')
def deleteJob(jid):
    sql = "delete from jobs where jid=%s" % jid
    setData(sql)
    flash('Job Deleted!')
    return redirect(url_for('adminJobs'))


@app.route('/admin/usersByCourse/<cid>/')
def viewUsersByCourse(cid):
    sql = "select * from user_details where cid=%s" % cid
    res = getData(sql)
    return render_template('admin/userByCourse.html',data=res)


@app.route('/admin/getCourseName/',methods=['POST'])
def getCourseName():
    cid = request.form['cid']
    sql = 'select name from courses where cid=%s' % cid
    res = getData(sql)[0][0]
    return res


@app.route('/user/home')
def userHome():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select cid from user_details where uid=%s" % session['uid']
    cid = getData(sql)[0][0]
    sql = "select eid,title,date,time,duration,s.name,c.name from exams e join subjects s on s.sid=e.sid join courses c on c.cid=s.cid where c.cid=%s and e.date = current_date order by e.date desc" % cid
    res = getData(sql)
    return render_template('user/home.html', exams=res)


@app.route('/user/exam/start/<eid>/')
def startExam(eid):
    txt = 'Please enter space bar to start exam'
    _thread.start_new_thread(speak, (txt,))
    return render_template('user/start_exam.html', eid=eid)


@app.route('/user/exam/result/')
def userResult():
    sql = "select rid,title,date,time,mark from results r join exams e on e.eid=r.eid where r.uid=%s" % session[
        'uid']
    res = getData(sql)
    return render_template('user/results.html', results=res)


@app.route('/user/jobs/')
def userJobs():
    sql = "select cid from user_details where uid=%s" % session['uid']
    cid = getData(sql)[0][0]
    sql = "select * from jobs where cid=%s" % cid
    res = getData(sql)
    return render_template('user/jobList.html', jobs=res)

@app.route('/user/jobs/apply/<jid>/')
def userApplyJob(jid):
    sql = "select ifnull(max(uj_id)0,)+1 from user_job_apply"
    uj_id = getData(sql)[0][0]
    sql = "insert into user_job_apply values(%s,%s,%s,current_date)"
    vals = (uj_id,session['uid'],jid)
    setData(sql,vals)
    return redirect(url_for('userJobs'))


@app.route('/user/feedback/')
def userFeedbacks():
    sql = "select * from feedbacks where uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/feedback.html',feedbacks=res)


@app.route('/user/sendFeedback/',methods=['POST','GET'])
def sendFeedback():
    if request.method == 'POST':
        msg = request.form['msg']
        sql = "select ifnull(max(fid),0)+1 from feedbacks"
        fid = getData(sql)[0][0]
        sql = "insert into feedbacks values(%s,%s,%s,current_date,NULL)"
        vals = (fid,session['uid'],msg)
        setData(sql,vals)
        return redirect(url_for('userFeedbacks'))
    return render_template('user/sendFeedback.html')


@app.route('/logout')
def logout():
    del session['uid']
    del session['role']
    return redirect(url_for('home'))


app.run(debug=True)
