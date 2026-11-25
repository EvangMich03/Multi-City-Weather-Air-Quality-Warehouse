CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitute FLOAT
);


CREATE TABLE weather (
    location_id int references locations (location_id),
    forecast_time TIMESTAMPTZ not null,
    tempar FLOAT,
    precipipation FLOAT,
    windspeed FLOAT, 
    primary key (location_id,forecast_time)
); 