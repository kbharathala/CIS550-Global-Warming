from . import main
from flask import Flask, render_template, url_for
import pymysql
from pymongo import MongoClient
import gridfs
import pandas
from sqlalchemy import create_engine

@main.route("/")
def hello():
    return "Hello World!"

@main.route("/country/<country>")
def country(country):
    connection = pymysql.connect(host="proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com", user="rip_us", password="abdu9000", db="proj", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    res = None
    country_info = {'Name': country}
    with connection.cursor() as cursor:
        sql = 'Select * from Country where Country.Name = \"' + country + '\";'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            res = res[0]
            for key in res.keys():
                country_info[key] = res[key]
        sql = 'Select U.fname, U.percent_usage from Uses U where U.cname = \"' + country + '\";'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for r in res:
                country_info[r['fname']] = float(r['percent_usage'])
    client = MongoClient('ec2-34-209-155-18.us-west-2.compute.amazonaws.com', 27017)
    db = client['proj']
    fs = gridfs.GridFS(db)
    flag_success = False
    try:
        img = fs.get(db['flags'].find_one({"country": country})['id']).read()
        filename = 'app/'+url_for("static", filename="images/temp.png")
        f = open(filename, "wb")
        f.write(img)
        f.close()
        flag_success = True
    except Exception:
        pass
    return render_template("country.html", country=country_info, flag=flag_success)

@main.route('/map')
def index():
    #create the connection string
    con=create_engine('mysql+mysqldb://wbuser:wbpwd@192.168.1.117:3306/wb',
    echo=False)
    #get data
    datar=pandas.read_sql('SELECT * FROM wbdt', con)
    #keep only data for 2014
    datar14=datar[datar.yr==2014]
    #assign the dataframe to a variable "table"
    return render_template('table.html',table=datar14)
