# Creating a Web Service with Flask, Postgres, Docker, Nginx, and Gunicorn

I created a basic and fully functioning production web service that allows you to create an account, make tweets, and search tweets from all urers. To accomplish this, I first created a development site on a local server and databse. I then conected the application to postgres and netcat allowing me to shift from the local site to a production site. I also used a `docker-compose.prod.yml` Dockerfile to distinguish my production and development code. This new Dockerfile used **multi-stage build** to help reduce my final Docker image size. I added **Nginx** to serve as a reverse proxy for Gunicorn to handle user requests and static files.

## Build Instructions

Once in the root folder, ensure no docker instances are running by entering
```
$ docker-compose -f docker-compose.prod.yml down -v
```
Confirm Docker has no instances with 
```
$ docker ps
```
Then, build the production code with the command
```
$ docker-compose -f docker-compose.prod.yml up -d --build
```
This calls the necessary production files and should build an instance of this web project. We will then start our Postgres database with the following command
```
$ docker-compose -f docker-compose.prod.yml exec web python manage.py create_db
```
In order to view the web service on your local browser use port forwarding on another terminal with the port specification `-L localhost:2727:localhost:2727`.

You can then visit `http://localhost:2727/upload` on any compatible browser (Chrome, Firefox, etc.) to upload your photo and view it at `http://localhost:2727/media/IMAGE_FILE_NAME`.
