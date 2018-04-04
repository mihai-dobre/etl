# etl

Etl is a django rest framework application. It has 2 parts:
* REST API
* elt management command
## REST API
Endpoints:
* `/stats/browser` : shows information about the browsers used
* `/stats/os` : shows information about the operating systems used
* `/stats/device` : shows information about the devices used
* `/docs/`: **interactive documentation** for the api

## etl management command
It is a django management command used for parsing and loading data into the database. It also prints on the screen(standard output) information about:
* Top 5 Countries based on number of events
* Top 5 Cities based on number of events
* Top 5 Browsers based on number of unique users
* Top 5 Operating systems based on number of unique users

## Commands:
* Create a postgres user: `docker-compose run db psql -h db -p 5432 -U postgres --command "CREATE USER yieldify WITH PASSWORD 'yieldify';CREATE DATABASE etl OWNER yieldify;GRANT ALL PRIVILEGES ON DATABASE etl TO yieldify;"`


### Installation:

Install the proper docker version following the [instructions](https://docs.docker.com/install/)
Will be 2 containers running:
1. Postgres9.6 container
2. Django app container running python 3.6 and django 1.11

### Configuration
#### Initialization scripts
Make sure the following scripts are allowed to execute(`chmod +x file.sh`):
* `run.sh`
* `docker-entrypoint-initdb.d/yieldify_init.sh`

#### .env file
API.env contains the credentials for database account. Was added to the repository just to ease the first run. For production use make sure you change the credentials.

#### django settings file
Path: `yieldify/settings/settings.py`
Contains all the django app settings.

#### django admin page(optional)
To be able to access the django admin page you need to create a django superuser using the command: `docker exec web python3 manage.py createsuperuser`

### Run
* docker containers: `docker-compose up` in project's root folder(wait for the containers to start)
* etl management command: `docker exec web python3 manage.py etl -dir '<directory_with_input_tsv.gz_input_files'`
* api: `http://localhost:8000` followed by one of the endpoints mentioned in _REST API_ section
* django admin page: `http://localhost:8000/admin`

### Logs
Application logs can be found in `logs/` folder.
Each endpoint has its own log file:
* `logs/browser.log`
* `logs/device.log`
* `logs/op_sys.log`
The management command has a separate log file:
* `logs/etl.log`
