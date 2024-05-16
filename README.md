# CORE BACK-END

## Table of Contents

- [Initial Setup](#initial-setup)
- [Setup on MacOs](#core-back-end-mac-os)
- [Resources for Debugging](#debugging-resources)

---

## Commands
These are the following commands that can be run with the `manage.py` file:
* `python manage.py send_pending_notifications` - Sends all pending notifications to the recipients
* `python manage.py setup_daily_booking_reminders` - Creates the notifications for the bookings that have events due today
* `python manage.py import_from_csv --contacts_file <path_to_contacts_csv> --locations_file <path_to_locations_csv> --companies_file <path_to_companies_csv` - Imports the contacts, locations and companies from the csv files.
* `python manage.py update_serializer` - Update the status for the bookings
* `python manage.py update_serviceroot` - Update the service root
  * The contacts table must have the columns: `id`, `email`, `email_context`, `phone`, `phone_context`, `fax`, `fax_context`.
  * The locations table must have the columns: `id`, `address`, `unit_number`, `city`, `state`, `country` (optional, defaults to "United States of America"), `zip`.
  * The companies table must have the columns: `name`, `type`, `send_method`, `on_hold` ("yes" or "no"), and `contact_ids` and `location_ids` which are comma separated lists of the ids of the previously defined contacts and locations respectively.
* `python manage.py import_languages_from_csv <path_to_csv>` - Imports the languages from the csv file.
  * The csv file must have the columns (please note that they are case-sensitive): `Show` ("TRUE" or empty), `Common` ("TRUE" or empty), `alpha2`, `Alpha3`, `English Name`, `English Description`.
  * When running the script, if there's another entry in the database that matches a row's `alpha2`, `Alpha3` and `English Name` columns, the script will update that entry with the new data.
* `python manage.py migrate_languages_to_model` - Meant to be a one time script. Migrates the language extras in the database to the new language model.
* `python manage.py check_submitted_notifications_status` - Checks the status of all submitted notifications and updates the database accordingly.

---

## Initial Setup

First of all install:
- PostgreSQL and pgAdmin4
- Python3
- Graphviz

Also, install the dependencies with the command `pip install -r requirements.txt`. If a new package was added to `requirements.txt`, run the same command previously mentioned.

To preload data for testing, run:\
`python manage.py migrate core_backend 0019`\
`python manage.py loaddata fixtures/core_backend_20230316_prefill_for_migration_0019.json --app core_backend`\
You can update your migrations after that.

### Disclaimer

This README file was originally written for a Linux installation on a Virtual Machine running on Windows. Scroll down for the Mac OS version. 

Before installing all the dependencies of the project, be sure that you are using Python 3.8.10. The dependencie backports.zoneinfo does not support superior versions than 3.8.10. Also check-out that you set up the path of PostgreSQL to your system.

**In pgAdmin4**,
create `core_user` role,

![image](https://user-images.githubusercontent.com/53912324/199030034-d79ba002-7ea6-4e8a-976d-264d23d85488.png)

with login and superuser priviledges,

![image](https://user-images.githubusercontent.com/53912324/199030193-4563a741-6dcf-4a3d-8563-6bab0d63bf95.png)

then create a server group with any name, with user `core_user` and password `core_password`,

![image](https://user-images.githubusercontent.com/53912324/199030464-8a51af7b-a48b-44cc-bc81-de4194839285.png)
![image](https://user-images.githubusercontent.com/53912324/199030669-789ce73f-33ef-4a23-a5e4-cd53e543fd74.png)
![image](https://user-images.githubusercontent.com/53912324/199030956-dc7b9243-e0be-4d89-82c9-3d4420bf1a07.png)

then, **at project's root directory, open a terminal** and run

`python manage.py migrate`

`python manage.py runserver localhost:8000`

## Everyday setup

To start running the backend, run `python manage.py runserver localhost:8000`

If you made modifications to the models in `core_backend/models.py`, before running the app, run 

`python manage.py makemigrations`

`python manage.py migrate`

---

# CORE BACK-END Mac OS

## Initial setup

Before trying to install the dependecnies you need to install the following:
- PostgreSQL and pgAdmin4
- Python3
- Graphviz package

### PostgreSQL and pgAdmin4

The easiest way to install PostgresSQL on Mac is trough the Postgres.App you can find a detailed tutorial [here](https://lifewithdata.com/2021/12/08/sql-tutorial-how-to-install-postgresql-and-pgadmin-on-mac/), including how to install pgAdmin4.

After the installations you need to set up the path of PostgreSQL to your system. Instructions on how to do this can be found [here](https://www.makeuseof.com/postgresql-macos-installing/).

### Python3

It is important that you use python version 3.8.10, you can find it and all the ohter versions at https://www.python.org. 

### Graphviz package

The easiest way to dowload packages on Mac OS is with the [Homebrew](https://brew.sh) package manager and we will be using to intsall Graphviz.

1. Install graphviz
`brew install graphviz`

2. Check the path to your graphviz by running:
`brew info graphviz`

In my case this was my path: `/opt/homebrew/Cellar/graphviz/7.0.1`

3. Change to your directory
`export GRAPHVIZ_DIR="/usr/local/Cellar/graphviz/<VERSION>"`. Replace the path between " " with the path you found in the second step. In my case the command i ran was: `export GRAPHVIZ_DIR="/opt/homebrew/Cellar/graphviz/7.0.1"` 

4. Finally install pygraphviz by running:
`pip3 install pygraphviz --global-option=build_ext --global-option="-I$GRAPHVIZ_DIR/include" --global-option="-L$GRAPHVIZ_DIR/lib"`

## Virtual Environment

All the dependencies will be installed after creating and activating a virtual environment.

When running python and pip commands I ran into the issue that my Mac's default python version (3.8.9) kept getting called instead of the one intended for use in this project (3.8.10). This caused me a bunch of different problems that i won't get into but all you need to prevent this is to run python3 or pip3 instead. 

Create the virtualenv by specifying the path to the correct python version and path to where you want it created.
`virtualenv --python3="/usr/bin/pythonX.X" "/path/to/new/virtualenv/"`

Here is an example of how the command looked when i ran it for my Mac:
`virtualenv --python3="/Library/Frameworks/Python.framework/Versions/3.8/bin/python3" "/Users/marcel/Desktop/CORE/core_backend`

Where `core_backend` is the projects root directory.

Move to the project's root directory and activate the venv specifying it's path with: 
`source /path/to/new/virtualenv/bin/activate`

Example: 
`source /Users/marcel/Desktop/CORE/core_backend/bin/activate`

Now we are finally ready to install the dependencies. Run:
`pip3 install -r requirements.txt`. If a new package was added to `requirements.txt`, run the same command previously mentioned.

**In pgAdmin4**,
create `core_user` role,

![image](https://user-images.githubusercontent.com/53912324/199030034-d79ba002-7ea6-4e8a-976d-264d23d85488.png)

with login and superuser priviledges,

![image](https://user-images.githubusercontent.com/53912324/199030193-4563a741-6dcf-4a3d-8563-6bab0d63bf95.png)

then create a server group with any name, with user `core_user` and password `core_password`,

![image](https://user-images.githubusercontent.com/53912324/199030464-8a51af7b-a48b-44cc-bc81-de4194839285.png)
![image](https://user-images.githubusercontent.com/53912324/199030669-789ce73f-33ef-4a23-a5e4-cd53e543fd74.png)
![image](https://user-images.githubusercontent.com/53912324/199030956-dc7b9243-e0be-4d89-82c9-3d4420bf1a07.png)

<br />

This step isn't in the original README, but as Mac OS user i was having the following error: `dingo.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: FATAL: database "core_db" does not exist`. I could only solve it by creating a `core_db` inside the `core_server`: 

<br />

![image](https://user-images.githubusercontent.com/64095070/202921443-9d0b500e-e89b-4c88-8428-425ffb7ef5ee.png)

then, **at project's root directory, open a terminal** and run

`python3 manage.py migrate`

`python3 manage.py runserver localhost:8000`

---

## Debugging Resources

Here are some useful resources for learning how to debug project.

- https://code.visualstudio.com/docs/python/tutorial-django
- https://www.youtube.com/watch?v=7qZBwhSlfOo
