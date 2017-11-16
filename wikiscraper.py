from bs4 import BeautifulSoup
import urllib2

def get_infobox(country):
  site = "http://en.wikipedia.org/wiki/" + country
  req = urllib2.Request(site, headers = {'User-Agent': 'Mozilla/5.0'})
  page = urllib2.urlopen(req)

  soup = BeautifulSoup(page.read(), "lxml")
  try:
    table = soup.find('table', class_='infobox geography vcard')
  except Exception as e:
    print(e)
    return

  result = {}
  for tr in table.find_all('tr'):
    if tr.find('th'):
      try: 
        result[tr.find('th').text.rstrip().lstrip()] = tr.find('td').text.rstrip()
      except:
        print('failed')
    
  return result

print(get_infobox("india"))