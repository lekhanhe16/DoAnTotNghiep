import csv
import json
from datetime import datetime as dt

import numpy as np
from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'
mysql = MySQL(app)


def get_account(user, pwd):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM Account, Admin WHERE username = %s AND password = %s AND Account.AdminId = Admin.PersonId",
        (str(user), str(pwd)))
    fetch_data = cur.fetchone()
    return fetch_data


def add_new_customer(timein, datein, gender, age, expressions, base64):
    emo_check = np.zeros(3, dtype=int)
    out_time = dt.strftime(dt.now(), '%H:%M:%S')
    out_date = dt.strftime(dt.now(), '%Y-%m-%d')
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Person VALUES (default)")
    mysql.connection.commit()
    last_insert_id = cur.lastrowid
    cur.execute("INSERT INTO Civilian VALUES(%s, %s, %s, %s, %s, %s)",
                (int(last_insert_id), str(timein), str(datein),
                 str(out_time), str(out_date), str(base64)))
    mysql.connection.commit()
    last_civil = last_insert_id
    if gender == 1:
        cil_gender = 1
    else:
        cil_gender = 2
    cur.execute("INSERT INTO Civilian_gender VALUES (default, %s, %s)",
                (int(last_civil), int(cil_gender)))
    mysql.connection.commit()
    cur.execute("INSERT INTO Age VALUES (default, %s, %s, %s)",
                (int(last_civil),
                 int(age - 3), int(age + 3)))
    mysql.connection.commit()
    for e in expressions:

        if str(e) == 'neutral':
            iemo = 0
        elif str(e) == 'happy':
            iemo = 1
        elif str(e) == 'sad':
            iemo = 2

        if emo_check[iemo] == 0:
            cur.execute("INSERT INTO Expression VALUES (default, %s, %s)",
                        (int(last_civil), str(e)))
            mysql.connection.commit()
        emo_check[iemo] = 1

    cur.close()


def get_customer_by_month_year(month, year):
    cur = mysql.connection.cursor()
    cur.execute("SELECT PersonId, GenderId, expression, lower, "
                "timein, datein, faceimg "
                "FROM Civilian, Civilian_gender, Expression, Age "
                "WHERE PersonId = Civilian_gender.CivilianId AND PersonId = Expression.CivilianId AND "
                "PersonId = Age.CivilianId AND MONTH(datein) = %s AND YEAR(datein) = %s ORDER BY PersonId",
                (int(month), int(year)))
    fetch_data = cur.fetchall()

    res = {}
    s = 0
    fetch_data = list(fetch_data)

    for i, d in enumerate(fetch_data):
        d = list(d)
        if d[1] == 1:
            d[1] = 'male'
        else:
            d[1] = 'female'
        d = tuple(d)
        if fetch_data[i - 1][0] == d[0] and i > 0:
            res[len(res) - 1] = list(res[len(res) - 1])
            res[len(res) - 1][2] = str(res[len(res) - 1][2]) + ', ' + str(d[2])
            res[len(res) - 1] = tuple(res[len(res) - 1])
        else:
            res[s] = d
            s += 1
    ret = json.dumps([{'no': res[data][0], 'expression': res[data][2],
                       'age': res[data][3], 'gender': res[data][1], 'timein': str(res[data][4]),
                       'datein': str(res[data][5]),
                       'faceimg': str(res[data][6]), 'isadd': int(0)} for data in res])
    cur.close()
    return ret


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
    return result


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

    with open(
            '/home/kl/PycharmProjects/Do an Tot nghiep PTIT/face_age_gender_emotion/visual_web/static/csv/agemonth.csv',
            'w',
            newline='') as file:
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
    return emo


def get_customer_byday(day):
    cur = mysql.connection.cursor()
    cur.execute("SELECT Distinct PersonId, GenderId, expression, lower, "
                "timein, datein, faceimg "
                "FROM Civilian, Civilian_gender, Expression, Age "
                "WHERE PersonId = Civilian_gender.CivilianId AND PersonId = Expression.CivilianId AND "
                "PersonId = Age.CivilianId AND datein = %s ORDER BY PersonId", (str(day),))
    # cur.execute("SELECT * "
    #             "FROM Civilian "
    #             "WHERE datein = %s", (str(day),))
    fetch_data = cur.fetchall()

    res = json.dumps([{'no': data[0], 'expression': data[2],
                       'age': data[3], 'gender': data[1], 'timein': str(data[4]), 'datein': str(data[5]),
                       'faceimg': data[6], 'isadd': 0} for data in fetch_data])
    return res
