from . import main
from flask import Flask, render_template, url_for, request, redirect, flash
import pymysql
from pymongo import MongoClient
import gridfs
import pandas
import os
from sqlalchemy import create_engine
from neo4j.v1 import GraphDatabase

print('Connecting to DataBases')
sql_connection = pymysql.connect(host="proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com", user="rip_us", password="abdu9000", db="proj", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
mongo_client = MongoClient('ec2-34-209-155-18.us-west-2.compute.amazonaws.com', 27017)
neo4j_driver = GraphDatabase.driver('bolt://ec2-34-201-111-94.compute-1.amazonaws.com:7687', auth=('neo4j','abdu9000'))

@main.route("/")
def index2():
    return render_template("main.html")

@main.route("/country/")
@main.route("/country_search")
def country_search():
    return render_template("country_search.html", country=None)

@main.route("/aggregate_filter")
def aggregate_filter():
    return render_template("aggregate_filter.html", agg=None)

@main.route("/country/<country>")
def country(country=None):
    global sql_connection
    global mongo_client
    global neo4j_driver
    if country is None:
        return country_search()
    connection = sql_connection
    res = None
    country_info = {'Name': country}
    with connection.cursor() as cursor:
        sql = 'Select * from Country where Country.Name = \"' + country + '\";'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is None or len(res) == 0:
            flash('No such country', 'error')
            return country_search()
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
    time_info = {"Year": [], "Emissions": [], 'TempYear': [], 'Temp': []}
    with connection.cursor() as cursor:
        sql = "Select * from Emissions E where E.Country = \"" + country + "\";"
        cursor.execute(sql)
        res = cursor.fetchall()
        sql2 = 'Select S.Year, AVG(S.Value) as avg from (Select E.Year, T.Value from (Select * from Emissions where Country = \"' + country + '\") E left join (Select * from Temp where Country = \"' + country.upper() + '\") T on E.Year = T.Year) S group by S.Year'
        cursor.execute(sql2)
        res2 = cursor.fetchall()
        if res is not None:
            for i in range(len(res)):
                time_info['Year'].append(int(res[i]['Year']))
                time_info['Emissions'].append(float(res[i]['Emissions']))
                if res2 is not None and len(res2) >= i+1 and res2[i]['avg'] is not None:
                    time_info['TempYear'].append(time_info['Year'][-1])
                    time_info['Temp'].append(float(res2[i]['avg'])/100.0)
    temp_info = None
    with connection.cursor() as cursor:
        sql = 'Select T.Year, T.Month, T.Value from Temp T inner join Month M on T.Month = M.Month where T.Country = \"' + country + '\" and T.Value is not NULL group by T.Country, T.Year, T.Month order by T.Year desc, M.MonthNum desc limit 1'
        cursor.execute(sql)
        res = cursor.fetchall()
        try:
            temp_info = {}
            temp_info['RecentYear'] = res[0]['Year']
            temp_info['RecentMonth'] = res[0]['Month']
            temp_info['Value'] = float(res[0]['Value'])/100.0
            sql = 'Select Year from Temp where Value is not NULL and Value >= ' + str(res[0]['Value']) + ' and Year <> ' + str(res[0]['Year']) + ' and Country = \"' + country.upper() + '\" and Month=\"' + res[0]['Month'] + '\" group by Country, Year, Month order by (Value-' + str(res[0]['Value']) + ') desc'
            cursor.execute(sql)
            res = cursor.fetchall()
            if res is not None:
                temp_info['HigherYears'] = []
                for y in res:
                    temp_info['HigherYears'].append(str(y['Year']))
        except:
            temp_info = None
            print('No Temp Info for ' + country)
    client = mongo_client
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
    merged = None
    impact = None
    driver = neo4j_driver
    query = """
    MATCH (input:CountryFuel {name:'""" + country + """'})-[exports:FuelExports]->(neighbor:CountryFuel)<-[neighborimports:FuelExports]-(:CountryFuel)
    RETURN neighbor.name, exports.value/(SUM(neighborimports.value)+exports.value) AS weight
    ORDER BY weight DESC
    """
    with connection.cursor() as cursor:
        sql_q = "SELECT Country, Emissions FROM Emissions WHERE Year=2015"
        cursor.execute(sql_q)
        neighbor_emissions = pandas.DataFrame(cursor.fetchall())
    with driver.session() as session:
        with session.begin_transaction() as tx:
            fuel_exports = pandas.DataFrame([(r['neighbor.name'], round(r['weight']*100,2)) for r in tx.run(query)])
            fuel_exports.columns = ['Country', 'Weight']
    merged = fuel_exports.merge(neighbor_emissions, on='Country')
    tmp = merged[merged['Country'] != 'World']
    impact = (tmp['Weight'] * tmp['Emissions'] / 100).sum()
    return render_template("country_search.html", country=country_info, img=filename, time_series=time_info, temp_info=temp_info, fuel_exports=merged, impact=impact)

@main.route('/aggregate')
def aggregate():
    metric = request.args.get('metric')
    max_val = request.args.get('max')
    min_val = request.args.get('min')
    metrics = ['HDI', 'LandArea', 'Population', 'GDP', 'Gini', 'overall_efficiency', 'Emissions']
    current_year = 2017
    query = "SELECT "
    count = 0
    for m in metrics:
        if count > 0:
            query += ", "
        query += "AVG(" + m + ") as "+m+"_AVG, MIN("+m+") as "+m+"_MIN, MAX("+m+") as "+m+"_MAX"
        count += 1
    from_part = " FROM (SELECT * FROM ((SELECT t.name2, SUM(t.efficiency) AS overall_efficiency FROM (SELECT u.cname AS name2, u.fname, u.percent_usage * f.Efficiency AS efficiency FROM Uses u inner join Form f on u.fname = f.Name) t GROUP BY t.name2) E inner join (SELECT M.Country, AVG(M.Emissions) as emissions FROM Emissions M WHERE M.Year >= " + str(current_year-10) + " GROUP BY M.Country) K on E.name2 = K.country) inner join Country C on E.name2 = C.Name) A WHERE "+m+" >= " + str(min_val) + " AND " + m + " <= " + str(max_val)
    query += from_part
    print(query)
    res = None
    connection = pymysql.connect(host="proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com", user="rip_us", password="abdu9000", db="proj", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        cursor.execute(query)
        res = cursor.fetchall()
    agg = res[0]
    stats = {}
    for m in metrics:
        stats[m] = {'max': agg[m+'_MAX'], 'min': agg[m+'_MIN'], 'avg': agg[m+'_AVG']}
    print(agg)
    res = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT Name" + from_part)
        res = cursor.fetchall()
    countries = []
    print(res)
    if res is not None:
        for r in res:
            countries.append(r['Name'])
    stats['Number of Countries'] = {'max': len(countries), 'min': len(countries), 'avg': len(countries)}
    return render_template("aggregate_filter.html", agg=stats, countries=countries)

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

@main.route('/comparison')
@main.route('/comparison_search')
def comparison_search():
    return render_template("comparison_search.html", country1=None, country2=None)

@main.route("/comparison/<country1>/<country2>")
def compare(country1=None, country2=None):
    if country1 is None or country2 is None:
        return comparison_search()
    connection = pymysql.connect(host="proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com", user="rip_us", password="abdu9000", db="proj", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    res = None
    time_info1 = {"Year": [], "Emissions": [], 'TempYear': [], 'Temp': []}
    with connection.cursor() as cursor:
        sql = "Select * from Emissions E where E.Country = \"" + country1 + "\";"
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for i in range(len(res)):
                time_info1['Year'].append(int(res[i]['Year']))
                time_info1['Emissions'].append(float(res[i]['Emissions']))
    time_info2 = {"Year": [], "Emissions": [], 'TempYear': [], 'Temp': []}
    with connection.cursor() as cursor:
        sql = "Select * from Emissions E where E.Country = \"" + country2 + "\";"
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for i in range(len(res)):
                time_info2['Year'].append(int(res[i]['Year']))
                time_info2['Emissions'].append(float(res[i]['Emissions']))
    time_info = [time_info1, time_info2]
    uses1, uses2 = {}, {}
    with connection.cursor() as cursor:
        sql = 'Select U.fname, U.percent_usage from Uses U where U.cname = \"' + country1 + '\";'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for r in res:
                uses1[str(r['fname'])] = float(r['percent_usage'])
    with connection.cursor() as cursor:
        sql = 'Select U.fname, U.percent_usage from Uses U where U.cname = \"' + country2 + '\";'
        cursor.execute(sql)
        res = cursor.fetchall()
        if res is not None:
            for r in res:
                uses2[str(r['fname'])] = float(r['percent_usage'])
    uses = {0:uses1, 1:uses2}

    return render_template("comparison_search.html", country1=country1, country2=country2, time_series=time_info, uses=uses)
