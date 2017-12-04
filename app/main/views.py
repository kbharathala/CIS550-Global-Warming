from . import main
from flask import Flask, render_template, url_for
import pymysql
from pymongo import MongoClient
import gridfs
import pandas
import os
from sqlalchemy import create_engine

@main.route("/")
def index2():
    return render_template("main.html")

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
        sql = 'SELECT t.name, SUM(t.efficiency) AS overall_efficiency FROM (SELECT u.cname AS name, u.fname, u.percent_usage * f.Efficiency AS efficiency FROM Uses u, Form f WHERE u.fname = f.Name) t WHERE t.name = \"' + country + '\"'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            country_info['Efficiency'] = res[0]['overall_efficiency']
    time_info = {"Year": [], "Emissions": []}
    with connection.cursor() as cursor:
        sql = "Select * from Emissions E where E.Country = \"" + country + "\";"
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for i in range(len(res)):
                time_info['Year'].append(int(res[i]['Year']))
                time_info['Emissions'].append(float(res[i]['Emissions']))
    client = MongoClient('ec2-34-209-155-18.us-west-2.compute.amazonaws.com', 27017)
    db = client['proj']
    fs = gridfs.GridFS(db)
    filename = None
    try:
        img = fs.get(db['flags'].find_one({"country": country})['id']).read()
        fileprefix = 'app'+url_for("static", filename="images/")
        res = os.system("rm -rf " + fileprefix + "*")
        filename = country
        f = open(fileprefix+country+".png", "wb")
        f.write(img)
        f.close()
        flag_success = True
    except Exception:
        pass
    return render_template("country.html", country=country_info, img=filename, time_series=time_info)

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