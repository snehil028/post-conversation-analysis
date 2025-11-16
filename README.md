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

### Prerequisites
Make sure these are installed:
- Python 3.10+
- Redis (via Docker or local install)
- pipenv
