# Conversation Analysis System (Assignment 2)

This Django + Celery project analyzes user–AI conversations automatically.  
It exposes REST APIs for uploading chats and runs a scheduled daily task (using Celery Beat) to compute conversation metrics like clarity, empathy, relevance, sentiment, and resolution.

---

## Project Overview

- **Backend:** Django + Django REST Framework  
- **Scheduler:** Celery + django-celery-beat  
- **Broker & Backend:** Redis  
- **Database:** SQLite (default Django DB)  
- **Language:** Python 3.10+  
- **Purpose:** Automatically analyze new conversations every midnight (IST)

---

## 1. Setup Instructions (Step-by-Step)

### Prerequisites
Make sure these are installed:
- Python 3.10+
- Redis (via Docker or local install)
- pipenv

### Clone & Install
```bash
git clone <your-repo-url>
cd assignment2
pipenv install
```   <!-- ✅ Close this code block here -->

### Database Setup
Run Django migrations to initialize your SQLite database:
```bash
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
pipenv run python manage.py migrate django_celery_beat


## to hit upload endpoint
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/analysis/upload/ -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes((Get-Content .\sample_chat.json -Raw)))


##to trigger analysis
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/analysis/analyze/ -ContentType 'application/json' -Body '{"conversation_id": 3}'

#Loomlink:
https://www.loom.com/share/71683b7ec8f94d32add8f38b27bd1253
