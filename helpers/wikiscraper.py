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


def get_infobox(country):
  site = "http://en.wikipedia.org/wiki/" + country
  r = requests.get(site)

  soup = bs(r.text, "lxml")
  try:
    table = soup.find('table', class_='infobox geography vcard')
  except Exception as e:
    print(e)
    return

  result = {}
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

print(get_infobox("India"))
