import requests as re
import psycopg2 as psy
import os
import logging
import dotenv
import openmeteo_requests
import requests_cache
from retry_requests import retry
import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO
)
dotenv.load_dotenv()

cache_session = requests_cache.CachedSession('.cache',expire_after= 3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


conn = psy.connect(
    database = os.getenv("dbname"),
    user = os.getenv("dbusername"),
    password = os.getenv("dbpassword"),
    port = 5432,
    host = "localhost"
)

curr = conn.cursor()

QUERY = "INSERT INTO LOCATIONS(city_name,latitude,longitute)" \
"VALUES(%s,%s,%s) ON CONFLICT(location_id) DO UPDATE SET city_name = EXCLUDED.city_name, latitude = EXCLUDED.latitude, longitute= EXCLUDED.longitute"

VALUES = [
("Berlin",52.52,13.41),
("Madrid",40.42,3.70),
("London",51.51,0.13),
("Rome",41.89,12.51),
("Paris",48.85,2.35),
]
curr.executemany(QUERY,VALUES)




#Fetches longitudes and latitdes dynamically straight from the database. (Might move insertions inside DBeaver exercise was unprecise)
curr.execute("SELECT * FROM LOCATIONS ORDER BY location_id")
data  = curr.fetchall()
ids = [item[0] for item in data]
latitudes = [item[2] for item in data]
longitudes = [item[3] for item in data]
names = [item[1] for item in data]

logging.info(ids)
logging.info(latitudes)
conn.commit()

url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": latitudes,
	"longitude": longitudes,
    "hourly": ["temperature_2m","precipitation","wind_speed_10m"]
}
responses = openmeteo.weather_api(url,params=params)

for loc_id, response in zip(ids, responses):
    
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipipation = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind = hourly.Variables(2).ValuesAsNumpy()
    hourly_data = {
        "date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )
    }

    
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation"] = hourly_precipipation
    hourly_data["wind_speed_10m"] = hourly_wind

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    hourly_dataframe.insert(loc=0,column="location_id",value=loc_id)
    #logging.info(hourly_dataframe)
    QUERY = "INSERT INTO WEATHER (location_id,FORECAST_TIME,TEMPAR,PRECIPIPATION,WINDSPEED)" \
    "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (location_id,forecast_time) DO UPDATE SET  tempar = excluded.tempar,precipipation=excluded.precipipation,windspeed=excluded.windspeed" 

    VALUES = list(hourly_dataframe.itertuples(index=False,name=None))
    curr.executemany(QUERY, VALUES)
    


conn.commit()
conn.close()