import pymysql
import requests
import re
from bs4 import BeautifulSoup as bs


def strip_brackets(text):
  text = re.sub('\[[^\]]+\]', '', text)
  return text


def to_numeric(text):
  text = strip_brackets(text)
  text = re.sub('\([^\)]+\)', '', text)
  multiplier = re.sub('[^a-z]', '', text)
  number = float(re.sub('[^\\d^.]', '', text))
  if multiplier == 'trillion':
    number = number * 1000000000000
  elif multiplier == 'billion':
    number = number * 1000000000
  elif multiplier == 'million':
    number = number * 1000000
  return number


def get_infobox(country, country2):
  site = "http://en.wikipedia.org/wiki/" + country
  r = requests.get(site)

  soup = bs(r.text, "lxml")
  try:
    table = soup.find('table', class_='infobox geography vcard')
  except Exception as e:
    print(e)
    return

  result = {}
  country = country2
  pop = table.find('th', string='Population').find_parent().find_next_sibling().find('td').text
  result['Population'] = int(to_numeric(pop))
  area = table.find('th', string='Area').find_parent().find_next_sibling().find('td').text
  result['Land Area'] = int(to_numeric(area))
  gdp = table.find('a', string='GDP').find_parent().find_parent().find_next_sibling().find('td').text
  result['GDP'] = int(to_numeric(gdp))
  gini = table.find('a', string='Gini').find_parent().find_next_sibling().text
  result['Gini'] = to_numeric(gini)
  hdi = table.find('a', string='HDI').find_parent().find_next_sibling().text
  result['HDI'] = to_numeric(hdi)
  desc = soup.find('b', string=country).find_parent().text
  result['Description'] = strip_brackets(desc)

  """
  result = {}
  for tr in table.find_all('tr'):
    if tr.find('th'):
      try: 
        result[tr.find('th').text.rstrip().lstrip()] = tr.find('td').text.rstrip()
      except:
        print('failed')
  """
    
  return result


def contains_multiple_words(s):
  return len(s.split(" ")) > 1

connection = pymysql.connect(host='proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com', user='rip_us', password='abdu9000', db='proj', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
# with connection.cursor() as cursor:
#     sql = 'ALTER TABLE Country ADD Population int, ADD GDP int, ADD Gini real, Add HDI real'
#     cursor.execute(sql)

bad_scraped_countries = set();

with connection.cursor() as cursor:
  sql = 'SELECT Name FROM Country'
  cursor.execute(sql)
  country_list = cursor.fetchall();
  for country in country_list:
    for key, country_name in country.items():
      if (contains_multiple_words(country_name)):
        word_set = country_name.split(" ")
        cname_underscored = word_set[0]
        for word in word_set[1:]:
          cname_underscored = cname_underscored + "_" + word
      else:
        cname_underscored = country_name

      try:
        result = get_infobox(cname_underscored, country_name)

      except Exception as e:
        print("Error: Could not pull data from Wiki for " + country_name)
        bad_scraped_countries.add(country_name)
        continue

      try:
        sql_add_info = 'UPDATE Country SET Description = \"' + result['Description'] + '\", LandArea = ' + str(result['Land Area']) + ', Population = ' + str(result['Population']) + ', GDP = ' + str(result['GDP']) + ', Gini = ' + str(result['Gini']) + ', HDI = ' + str(result['HDI']) + ' WHERE Name = \"' + country_name + '\" ;'
        cursor.execute(sql_add_info)
      except Exception as e:
        continue





connection.commit();

  # try:


  # except Exception as e:
  #   print(e)
  #   return



# try:
#   print(get_infobox("India", "India"))
#   print(get_infobox("United_States_of_America", "United States"))
# except Exception as e: 
#   print(e)










