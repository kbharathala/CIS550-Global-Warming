from pymongo import MongoClient
import gridfs
import pandas as pd
import urllib
import cStringIO
from PIL import Image

client = MongoClient('ec2-34-209-155-18.us-west-2.compute.amazonaws.com', 27017)

db = client['proj']
fs = gridfs.GridFS(db)

countries_df = pd.read_csv('country_codes.csv')
# Namibia issue
countries_df = countries_df.set_value(153, 'alpha-2', 'NA')
for i in range(len(countries_df)):
    print(countries_df.iloc[i]['name'])
    image = urllib.urlopen("http://www.geognos.com/api/en/countries/flag/"+countries_df.iloc[i]['alpha-2']+'.png')
    with open("temp.png", "wb") as f:
        while True:
            chunk = image.read(16*1024)
            if not chunk:
                break
            f.write(chunk)
    f = open("temp.png", "rb")
    # image = Image.open(image)
    image_id = fs.put(f, filename=countries_df.iloc[i]['name']+str('_flag'))
    db.flags.insert_one({"country": countries_df.iloc[i]['name'], "id": image_id})


