# FileNest Project Setup Guide

## Prerequisites

Ensure you have the following installed on your machine:

Python 3.13 or later

Git (for version control)

Virtual Environment (venv)

### Clone the Repository
[Repository link](https://github.com/tonidevvn/FileNest)
```
git clone [Repository link]
cd FileNest
```

### Create and Activate Virtual Environment

```
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate    # On Windows
```

### Install Dependencies

```
pip install --upgrade pip
pip install -r requirements.txt
```

### Create a Superuser (For Admin Panel - Optional)

Follow the prompts to set up the admin account.
```
python manage.py createsuperuser
```

### Start the Development Server

Follow the prompts to access the app at: http://127.0.0.1:8000/
```
python manage.py runserver
```

