# PoultrySync - Multi-Tenant Ordering System

A Django-based multi-tenant application for managing orders and products across multiple companies with role-based access control and data isolation.

<img width="714" height="703" alt="image" src="https://github.com/user-attachments/assets/e95cb881-ce75-4dd4-8634-bf4a3da855ac" />


## Tech Stack

- Python 3.10.10
- Django 4.1.13
- Django REST Framework
- MySQL 5.7 (Aiven hosted)
- Docker & Docker Compose
- Gunicorn with WhiteNoise

## Prerequisites

- Docker Desktop
- Docker Compose
- Git

## Setup and Run with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/ibrahimsaber1/poultrysync-ordering.git
cd poultrysync-ordering
```

### 2. Configure Environment Variables

Add the `.env` file with the credentials sent to u via email :

```env
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your-host
DB_PORT=12345
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 3. Build Docker Image

```bash
docker-compose build
```

### 4. Run Database Migrations (you can skip this step if u are using the deployed db from the .env file)

```bash
docker-compose run --rm web python manage.py makemigrations
docker-compose run --rm web python manage.py migrate
```

### 5. Create Superuser (if u want to)
 > note: u will find a super user username and password in the email I sent to u as well. 

```bash
docker-compose run --rm web python manage.py createsuperuser
```

### 6. Start the Application

```bash
docker-compose up -d
```

The application will be available at:
- Homepage: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

### 7. Stop the Application

```bash
docker-compose down
```

## Demo Accounts

After loading demo data, use these credentials:

**Company 1: Sunrise Poultry Farm**
- Admin: `admin1` / `admin123`
- Operator: `operator1` / `operator123`
- Viewer: `viewer1` / `viewer123`

**Company 2: Golden Egg Productions**
- Admin: `admin2` / `admin123`



