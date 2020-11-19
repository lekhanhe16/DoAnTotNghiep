import os
import csv
import json
from flask import Flask, g, redirect, flash, jsonify, render_template, request, session, abort, url_for
from flask_mysqldb import MySQL
from functools import wraps
import time
from datetime import datetime as dt
import numpy as np

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'
mysql = MySQL(app)


def login_required(f):
    @wraps(f)
    def decorate_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorate_function

@app.route('/today')
def show_today():
    return render_template('today.html')

@app.route('/ageweek')
def show_age_week():
    # return render_template('ageweek.html')
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT PersonId, timein, datein, timeout, dateout, lower, higher, Gender.gender "
        "FROM Civilian, Age, Civilian_gender, Gender "
        "WHERE Civilian.PersonId = Age.CivilianId "
        "AND Civilian_gender.CivilianId = Civilian.PersonId "
        "AND Civilian_gender.GenderId = Gender.Id "
        "AND YEARWEEK(dateout, 1) = YEARWEEK(CURDATE(), 1)")
    fetch_data = cur.fetchall()

    cur.close()
    result = json.dumps([{'personid': data[0],
                          'lower': data[5], 'higher': data[6], 'gender': data[7]} for data in fetch_data])
    # print(result)
    return render_template('ageweek.html', tabledata=result)


@app.route('/ageoverall')
def ageoverall():
    cur = mysql.connection.cursor()
    cur.execute("SELECT lower, Gender.gender, Month(dateout) "
                "FROM Civilian, Age, Civilian_gender, Gender "
                "WHERE Civilian.PersonId = Age.CivilianId "
                "AND Civilian_gender.CivilianId = Civilian.PersonId "
                "AND Civilian_gender.GenderId = Gender.Id "
                "ORDER BY Month(Civilian.dateout)")
    fetch_data = cur.fetchall()
    cur.close()
    # result = json.dumps([{
    #             'lower': data[5], 
    #             'gender': data[7], 'month':data[8]} for data in fetch_data])
    # print(result)

    female = np.zeros([13, 6], dtype=int)
    male = np.zeros([13, 6], dtype=int)

    for d in fetch_data:
        age = d[0] + 3
        if 10 <= age <= 15:
            if d[1] == 1:
                male[d[2]][0] += 1
            else:
                female[d[2]][0] += 1
        elif 16 <= age <= 20:
            if d[1] == 1:
                male[d[2]][1] += 1
            else:
                female[d[2]][1] += 1
        elif 21 <= age <= 25:
            if d[1] == 1:
                male[d[2]][2] += 1
            else:
                female[d[2]][2] += 1
        elif 26 <= age <= 30:
            if d[1] == 1:
                male[d[2]][3] += 1
            else:
                female[d[2]][3] += 1
        elif 31 <= age <= 35:
            if d[1] == 1:
                male[d[2]][4] += 1
            else:
                female[d[2]][4] += 1
        elif 36 <= age <= 40:
            if d[1] == 1:
                male[d[2]][5] += 1
            else:
                female[d[2]][5] += 1

    with open('static/csv/agemonth.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["x1", "y1", "z1", "x2", "y2", "z2"])
        for i in range(1, 13):
            for j in range(6):
                if male[i][j] != 0 and female[i][j] != 0:
                    writer.writerow([i, j, male[i][j], i, j, female[i][j]])
                elif male[i][j] != 0 and female[i][j] == 0:
                    writer.writerow([i, j, male[i][j], '', '', ''])
                elif male[i][j] == 0 and female[i][j] != 0:
                    writer.writerow(['', '', '', i, j, female[i][j]])
    return render_template('agemonth.html')


@app.route('/logi')
def logi():
    return render_template('login.html')


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('index.html')


@app.route('/login', methods=['POST'])
def do_login():
    user = request.form['email']
    pwd = request.form['pass']
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM Account, Admin WHERE username = %s AND password = %s AND Account.AdminId = Admin.PersonId",
        (str(user), str(pwd)))
    fetch_data = cur.fetchone()
    try:
        if len(fetch_data) == 5:
            session['logged_in'] = True
    except:
        flash('Tài khoản hoặc mật khẩu sai')
    return home()


@app.route('/expression')
def expression():
    we = [0, 0, 0]
    cur = mysql.connection.cursor()
    cur.execute("SELECT expression FROM Expression, Civilian WHERE CivilianId = PersonId "
                "AND YEARWEEK(dateout, 1) = YEARWEEK(CURDATE(), 1)")
    week_data = cur.fetchall()
    for d in week_data:
        if d[0] == 'neutral':
            we[0] += 1
        elif d[0] == 'happy':
            we[1] += 1
        elif d[0] == 'sad':
            we[2] += 1

    me = [0, 0, 0]
    cur.execute("SELECT expression FROM Expression, Civilian WHERE CivilianId = PersonId "
                "AND MONTH(dateout) = MONTH(NOW())")
    month_data = cur.fetchall()
    for d in month_data:
        if d[0] == 'neutral':
            me[0] += 1
        elif d[0] == 'happy':
            me[1] += 1
        elif d[0] == 'sad':
            me[2] += 1
    emo = json.dumps(
        {"wneutral": we[0], "whappy": we[1], "wsad": we[2], "mneutral": me[0], "mhappy": me[1], "msad": me[2]})
    print(emo)
    return render_template('expression.html', data=emo)


@app.route('/logout')
def do_logout():
    session['logged_in'] = False
    return home()


if __name__ == "__main__":
    app.secret_key = 'kHaNhLeDePtRaI'
    app.run(debug=True, host='0.0.0.0', port=8855)
