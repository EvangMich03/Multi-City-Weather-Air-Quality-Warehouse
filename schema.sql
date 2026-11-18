CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude BIGINT,
    longitute BIGINT
)


CREATE TABLE weather (
    location_ref VARCHAR(100) PRIMARY KEY,
    forecast_time TIMESTAMP,
    temp FLOAT,
    precipipation FLOAT,
    windspeed INT 
)

