CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitute FLOAT
)


CREATE TABLE weather (
    location_ref VARCHAR(100) PRIMARY KEY,
    forecast_time TIMESTAMP PRIMARY KEY,
    temp FLOAT,
    precipipation FLOAT,
    windspeed FLOAT 
)

