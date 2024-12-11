# Airport API

## Project Overview

An API for managing airport operations written on DRF

## Installing using GitHub
Install PostgreSQL and create db


```shell
git clone https://github.com/Morphin20th/airport-api
cd airport-api
python3 -m venv venv
```

Linux/Mac:

```shell
source venv/bin/activate
```

Windows:

```shell
venv\Scripts\activate
```

.env:

```shell
pip install -r requirements.txt
set SECURITY_KEY=<key>
set POSTGRES_DB=<db_name>
set POSTGRES_DB_PORT=<db_port>
set POSTGRES_USER=<db_user>
set POSTGRES_PASSWORD=<db_password>
set POSTGRES_HOST=<db_host>
set PGDATA=<path>
python ./manage.py migrate
python ./manage.py runserver
```

## Run with docker
```shell
docker-compose build
docker-compose up
```

## Use fixtures
```shell
docker-compose exec airport python manage.py loaddata initial_data.json
```

## Getting access
- create user via /api/user/register/
- get access token via /api/user/token/


## Features

- **JWT authentication**
- **Admin panel**: /admin/
- **Documentation**: Swagger: /api/doc/swagger/ ; Redoc: /api/doc/redoc/ 
- **Managing orders and tickets**: Users can create orders.
- **Creating airplanes with airplane types**
- **Creating routes with airports**
- **Creating flights with crew**
- **Filter airplanes by name and type**
- **Filter routes by source and destination**
- **Filter flights by routes, airplanes, departure dates**
- **Upload images to airplanes**: api/airplanes/id/upload-image/
