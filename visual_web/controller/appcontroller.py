import base64
import csv
import io
import json
from datetime import datetime as dt
import pickle as pkl
import numpy as np
from PIL import Image
from cv2 import cv2
from flask import Flask
from flask_mysqldb import MySQL
from visual_web.model import *
from visual_web.controller import face_embedding as FE
from visual_web.model.customer import Customer

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

customers = []


def match_a_customer(civilian):
    global customers

    if len(customers) == 0:
        return None
    for i in range(len(customers)):
        if FE.is_match(civilian.face_embed, customers[i].embbed) is True:
            return Customer(cid=customers[i].civilianid, cusname=customers[i].name, cusphone=customers[i].phone,
                            emb=None, addr=customers[i].address)
        # print(i)

    return None


def get_customers():
    global customers
    customers.clear()
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT CivilianPersonId, name, phone, faceembed, address "
                "from Civilian, Customer, Person WHERE Person.id = Civilian.PersonId "
                "AND Civilian.PersonId = CivilianPersonId")
    fetch_data = cur.fetchall()
    # print(len(fetch_data))
    if len(fetch_data) > 0:
        for d in fetch_data:
            # 0 customer id, 1 name, 2 phone, 3 faceimg
            id = d[0]
            name = d[1]
            phone = d[2]
            # print(d[3])
            femb = pkl.loads(d[3])
            # print("get emb:" + str(femb))
            address = d[4]
            customer = Customer(id, name, phone, femb, address)
            customers.append(customer)


def get_admin_by_account(account):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT PersonId, AccountId, Name FROM Account, Admin WHERE username = %s AND password = %s "
        "AND Account.Id = Admin.AccountId",
        (str(account.username), str(account.pwd)))
    fetch_data = cur.fetchone()
    return fetch_data


def add_new_customer(customer):
    with app.app_context():
        # mysql.connection.begin()
        print("new cus emb" + str(customer.embbed))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Customer VALUES(%s, %s, %s, %s, %s)",
                    (customer.civilianid, customer.name, customer.phone,
                     pkl.dumps(customer.embbed), customer.address))
        mysql.connection.commit()
        # mysql.connection.rollback()
        # print(cur.lastrowid)
    # return "called"


# def add_expression(civilian):
#     with app.app_context():
#         cur = mysql.connection.cursor()
#         for e in civilian.expres:
#             cur.execute("INSERT INTO Expression VALUES (default, %s, %s, %s)",
#                         (int(civilian.id), str(e), str()))
#         mysql.connection.commit()


def add_new_civilian(civilian, addperson):
    # print(civilian.gender.gender)
    # print(expressions)
    with app.app_context():
        # mysql.connection.begin()
        emo_check = np.zeros(3, dtype=int)
        out_time = dt.strftime(dt.now(), '%H:%M:%S')
        out_date = dt.strftime(dt.now(), '%Y-%m-%d')
        cur = mysql.connection.cursor()
        # last_insert_id = 0
        if addperson == 1:
            cur.execute("INSERT INTO Person VALUES (default)")

            # print("last person "+str(cur.lastrowid))
            last_insert_id = cur.lastrowid
            # mysql.connection.commit()
        else:
            last_insert_id = civilian.id
        # mysql.connection.commit()
        # last_civil = last_insert_id
        if civilian.gender.gender == 1:
            cil_gender = 1

        else:
            cil_gender = 2

        cur.execute("INSERT INTO Civilian VALUES(default,%s, %s, %s, %s, %s, %s, %s,%s,%s)",
                    (int(last_insert_id), int(cil_gender), str(civilian.timein), str(civilian.datein),
                     str(out_time), str(out_date), str(civilian.faceimg), int(civilian.lower), int(civilian.higher)))
        # mysql.connection.commit()

        # mysql.connection.commit()
        for i, e in enumerate(civilian.expres):

            if str(e) == 'neutral':
                iemo = 0
            elif str(e) == 'happy':
                iemo = 1
            elif str(e) == 'sad':
                iemo = 2
            if str(e) == 'sad' and i == len(civilian.expres) - 1:
                continue
            if emo_check[iemo] == 0:
                # print("emo cvi: " + str(last_civil))
                cur.execute("INSERT INTO Expression VALUES (default, %s, %s, %s, %s)",
                            (int(last_insert_id), str(e), str(civilian.timein), str(civilian.datein)))
                # mysql.connection.commit()
            emo_check[iemo] = 1
            emo_check[iemo] = 1
        # mysql.connection.commit()
        cur.close()
        # mysql.connection.rollback()
        return last_insert_id


def get_civilian_by_month_year(month, year):
    cur = mysql.connection.cursor()
    cur.execute("SELECT PersonId, GenderId, expression, lower, "
                "timein, datein, faceimg, Customer.CivilianPersonId, Customer.name from "
                "(SELECT PersonId, GenderId, expression, lower, "
                "timein, datein, faceimg "
                "FROM Civilian, Expression  "
                "WHERE PersonId = Expression.CivilianPersonId AND timein = moment AND datemoment = datein AND "
                "MONTH(datein) = %s AND YEAR(datein) = %s) as l left join Customer on "
                "Customer.CivilianPersonId = PersonId ORDER BY PersonId, datein, timein ",
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
        if fetch_data[i - 1][0] == d[0] and i > 0 and fetch_data[i - 1][4] == d[4] and fetch_data[i - 1][5] == d[5]:
            res[len(res) - 1] = list(res[len(res) - 1])
            res[len(res) - 1][2] = str(res[len(res) - 1][2]) + ', ' + str(d[2])
            res[len(res) - 1] = tuple(res[len(res) - 1])
        else:
            res[s] = d
            s += 1
    ret = json.dumps([{'no': res[data][0], 'expression': res[data][2],
                       'age': res[data][3], 'gender': res[data][1], 'timein': str(res[data][4]),
                       'datein': str(res[data][5]),
                       'faceimg': str(res[data][6]), 'isadd': int(0), 'cusid': str(res[data][7]),
                       'cusname': str(res[data][8])} for data in res])
    cur.close()
    return ret


def show_age_week():
    # return render_template('ageweek.html')
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT PersonId, timein, datein, timeout, dateout, lower, higher, Gender.gender "
        "FROM Civilian, Gender "
        "WHERE "
        "Civilian.GenderId = Gender.Id "
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
                "FROM Civilian, Gender "
                "WHERE "
                "Civilian.GenderId = Gender.Id "
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


def get_product_expression():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT t.id, t.Productname, t.expression, COUNT(t.expression) from (select Product.id, Product.Productname, "
        "expression from Product, Cart_Product, Cart, CustomerOrder, Customer, Civilian, Expression " +
        "WHERE CustomerOrder.CustomerId = Customer.CivilianPersonId AND CustomerOrder.CartId = Cart.id " +
        "AND Cart_Product.CartId = Cart.id AND Cart_Product.ProductId = Product.id " +
        "AND CustomerOrder.custimein = Civilian.timein AND CustomerOrder.orderdate = Civilian.datein " +
        "AND Civilian.PersonId = Customer.CivilianPersonId AND Expression.CivilianPersonId = Customer.CivilianPersonId " +
        "AND Expression.moment = CustomerOrder.custimein And Expression.datemoment = CustomerOrder.orderdate) " +
        "as t GROUP BY t.Productname, t.expression ORDER BY id, t.expression")
    fetch_data = cur.fetchall()
    res = json.dumps([{"id": data[0], "productname": data[1],
                       "expression": data[2], "count": data[3]} for data in fetch_data])

    return res


def expression():
    we = [0, 0, 0]
    cur = mysql.connection.cursor()
    cur.execute("SELECT expression FROM Expression, Civilian WHERE CivilianPersonId = PersonId "
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
    cur.execute("SELECT expression FROM Expression, Civilian WHERE CivilianPersonId = PersonId "
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
    # print(emo)
    return emo


def check_data(data, i):
    if data is not None and i == 7:
        return int(data)
    elif data is not None and i > 7:
        return str(data)
    else:
        return 0


def get_all_products():
    # with app.app_context():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Product")
    fetch_data = cur.fetchall()
    # print(fetch_data[0][0])

    cur.close()
    return json.dumps([{"id": data[0], "productname": data[1], "price": data[2]} for data in fetch_data])


def add_new_order(order):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Cart VALUES (default)")
    mysql.connection.commit()
    last_cart = cur.lastrowid
    # print("Cart " + str(last_cart))
    cart_products = order.cart.cart_products

    for cp in cart_products:
        cur.execute("INSERT INTO Cart_Product VALUES (default, %s, %s, %s)", (int(last_cart), int(cp.product),
                                                                              int(cp.quantity)))
        # mysql.connection.commit()

    cur.execute("INSERT INTO CustomerOrder VALUES (default, %s, %s, %s, %s, %s, %s)",
                (int(order.customer), int(last_cart), int(order.totalprice), str(order.custimein), str(order.ordertime)
                 , str(order.orderdate)))

    mysql.connection.commit()


def get_civilian_byday(day):
    cur = mysql.connection.cursor()
    cur.execute(
        "Select PersonId, GenderId, expression, lower, timein, datein, "
        "faceimg, Customer.CivilianPersonId, name, phone, address "
        "from (SELECT Distinct PersonId, GenderId, expression, lower, " +
        "timein, datein, faceimg " +
        "FROM Civilian, Expression, Gender "
        "WHERE (Civilian.GenderId = Gender.Id AND PersonId = Expression.CivilianPersonId and timein = moment) " +
        "AND datein = %s and datemoment = datein) as L " +
        "LEFT JOIN Customer "
        "on Customer.CivilianPersonId = PersonId "
        "ORDER BY PersonId",
        (str(day),))

    fetch_data = cur.fetchall()

    res = json.dumps([{'no': data[0], 'expression': data[2],
                       'age': data[3], 'gender': data[1], 'timein': str(data[4]), 'datein': str(data[5]),
                       'faceimg': data[6], 'cid': data[7], 'name': str(data[8]),
                       'phone': str(data[9]), 'address': str(data[10]), 'pos': i + 1} for i, data in
                      enumerate(fetch_data)])
    get_customers()

    return res
