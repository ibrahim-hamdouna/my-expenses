# My Expenses

My Expenses is a responsive expense-management application built with Django. It helps users record daily expenses, organize spending into categories, monitor their monthly budget, and export financial reports.

## Live Demo

[Open My Expenses](https://my-expenses-fgn4.onrender.com)

### Demo Account

Use the following account to explore the application without creating a personal account:

- **Username:** `demo`
- **Password:** `demo123456`

The demo account contains shared sample data. Other visitors may add, edit, or delete its content.

> The application runs on a free Render instance. The first request after a period of inactivity can take about one minute while the service starts.

## Features

- User registration and secure authentication
- Personal expense creation, editing, and deletion
- Custom categories with selectable colors
- Expense filtering by month and category
- Monthly spending and budget statistics
- Salary and remaining-budget tracking
- Recent-transaction overview
- PDF and Excel report exports
- Responsive layouts for desktop and mobile devices

## Technology Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** MySQL for local development and PostgreSQL on Render
- **Frontend:** Django templates, HTML, CSS, and JavaScript
- **Reports:** ReportLab and OpenPyXL
- **Production:** Gunicorn, WhiteNoise, and Render

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/ibrahim-hamdouna/my-expenses.git
cd my-expenses
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install the development dependencies

```powershell
pip install -r requirements-dev.txt
```

### 4. Create the MySQL database

Create a database named `my_expenses_db`, or use another name and update the environment variables below.

### 5. Configure the environment

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=replace-this-with-a-development-secret
ALLOWED_HOSTS=127.0.0.1,localhost

MYSQL_DATABASE=my_expenses_db
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

The `.env` file is ignored by Git. Never commit passwords, database credentials, or production secrets.

### 6. Apply database migrations

```powershell
python manage.py migrate
```

### 7. Start the development server

```powershell
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Deployment

The project is configured for deployment on Render through `render.yaml`:

- The web service runs with Gunicorn.
- Static files are collected during the build and served with WhiteNoise.
- Production data is stored in PostgreSQL.
- Commits pushed to the `main` branch trigger automatic deployments.
- `DEBUG` is disabled in production.

Required production configuration includes a secure `SECRET_KEY` and `DATABASE_URL`. These values must be stored as Render environment variables and must not be committed to GitHub.

## Demo Account Setup

Before publishing the demo credentials, register the following normal user through the live application:

```text
Username: demo
Password: demo123456
```

Do not give this account staff or administrator permissions. Add sample categories and expenses, avoid personal information, and periodically restore its sample data if visitors modify it.

## Author

Developed by [Ibrahim Hamdouna](https://github.com/ibrahim-hamdouna).
