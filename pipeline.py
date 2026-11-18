import requests as re
import psycopg2 as psy
import os
import logging
import dotenv


dotenv.load_dotenv()






conn = psy.connect(
    database = os.getenv("dbname"),
    user = os.getenv("dbusername"),
    password = os.getenv("dbpassword"),
    port = 5432,
    host = "localhost"
)

curr = conn.cursor()


weather = re.get("https://open-meteo.com")
logging.warning(weather.json())