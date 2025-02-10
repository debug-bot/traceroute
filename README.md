# Django Docker Setup

This project is a Django application containerized using Docker. This README provides instructions for building, and running Docker containers. In addition to the usual setup, this project uses an entrypoint script in `entrypoint.sh` to run Django management commands (such as database migrations, creating a superuser, populating the database with initial commands data, and collecting static files) automatically when the container starts.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.
- [Git](https://git-scm.com/) to clone the repository.

## Getting Started

### 1. Clone the Repository

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/debug-bot/traceroute.git && cd traceroute
```

### 2. Build and Run Docker Containers

Use docker-compose to build the images and run the Docker containers:

```bash
docker-compose up --build
```

This command will build the Docker images (if they haven't been built yet) and start the containers for the Django app and any additional services defined in the
 `docker-compose.yml` file.

### 3. Access the Django App

The Django app will be available at [http://127.0.0.1](http://127.0.0.1). The Django admin interface can be accessed
 at [http://127.0.0.1/admin](http://127.0.0.1/admin) with the default superuser credentials: `admin`/`admin123`. You can change the default superuser password in admin interface or by running the following command:
```bash
docker exec -it django_app python manage.py changepassword admin
```


