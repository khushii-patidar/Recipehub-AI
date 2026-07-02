============================================
  RecipeHub – Recipe Generator App
============================================

PAGES:
  /              → Homepage (latest + top recipes)
  /recipes/      → Recipe Explorer (search + filter)
  /recipes/add/  → Apni recipe add karo
  /recipes/<id>/ → Recipe detail (ingredients + steps)
  /ai-kitchen/   → AI ingredient-based generator
  /chat/         → Community chat rooms
  /profile/      → My / Liked / Saved recipes
  /login/        → Login
  /register/     → Register

RUN KARNE KE STEPS:
  1. unzip karein aur folder mein jaayein:
       cd foodshare_app

  2. Virtual env banao:
       python -m venv venv

  3. Activate karein:
       Windows:   venv\Scripts\activate
       Mac/Linux: source venv/bin/activate

  4. Django install karein:
       pip install django

  5. Database migrate karein:
       python manage.py migrate

  6. Server run karein:
       python manage.py runserver

  7. Browser mein kholo:
       http://127.0.0.1:8000/

============================================
