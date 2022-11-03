# core_backend

## Everyday setup

To start running the backend, run `python manage.py runserver localhost:8000`

If you made modifications to the models in `core_backend/models.py`, before running the app, run 

`python manage.py makemigrations`

`python manage.py migrate`

If a new package was added to `requirements.txt`, run `pip install -r requirements.txt`

## Initial setup

Install:
- pgAdmin4
- Postgresql
- Python3

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
