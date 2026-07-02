from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms

from .models import Recipe, SavedRecipe

import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('/login/')
# =========================
# ENV LOAD
# =========================
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms

from .models import Recipe, SavedRecipe

import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect('/login/')


# =========================
# ENV LOAD
# =========================
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise Exception("❌ OPENROUTER_API_KEY missing in .env file")


# =========================
# OPENROUTER CLIENT
# =========================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# =========================
# FORM
# =========================
class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'name',
            'emoji',
            'category',
            'cook_time',
            'description',
            'ingredients',
            'steps'
        ]


# =========================
# HOME
# =========================
def home(request):
    recent = Recipe.objects.all()[:6]
    top = Recipe.objects.all()
    top = sorted(top, key=lambda r: r.like_count(), reverse=True)[:3]
    total = Recipe.objects.count()

    return render(request, 'home.html', {
        'recent': recent,
        'top': top,
        'total': total
    })


# =========================
# REGISTER
# =========================
def register(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')

    return render(request, 'register.html', {'form': form})


# =========================
# RECIPE LIST
# =========================
def recipe_list(request):
    qs = Recipe.objects.all()

    cat = request.GET.get('cat', '')
    q = request.GET.get('q', '')

    if cat:
        qs = qs.filter(category=cat)

    if q:
        qs = qs.filter(name__icontains=q)

    return render(request, 'recipe_list.html', {
        'recipes': qs,
        'cat': cat,
        'q': q,
        'categories': Recipe.CATEGORY,
    })


# =========================
# RECIPE DETAIL
# =========================
def recipe_detail(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    ings = [i.strip() for i in r.ingredients.splitlines() if i.strip()]
    steps = [s.strip() for s in r.steps.splitlines() if s.strip()]

    liked = (
        request.user.is_authenticated and
        r.likes.filter(pk=request.user.pk).exists()
    )

    saved = (
        request.user.is_authenticated and
        SavedRecipe.objects.filter(user=request.user, recipe=r).exists()
    )

    similar = Recipe.objects.filter(category=r.category or "").exclude(pk=pk)[:3]

    return render(request, 'recipe_detail.html', {
        'r': r,
        'ings': ings,
        'steps': steps,
        'liked': liked,
        'saved': saved,
        'similar': similar,
        'user': request.user,  # ✅ Fix: passes user so Delete button shows for author
    })


# =========================
# LIKE
# =========================
@login_required
def recipe_like(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    if r.likes.filter(pk=request.user.pk).exists():
        r.likes.remove(request.user)
    else:
        r.likes.add(request.user)

    return redirect('recipe_detail', pk=pk)


# =========================
# SAVE
# =========================
@login_required
def recipe_save(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    obj, created = SavedRecipe.objects.get_or_create(
        user=request.user,
        recipe=r
    )

    if not created:
        obj.delete()

    return redirect('recipe_detail', pk=pk)


# =========================
# ADD RECIPE
# =========================
@login_required
def add_recipe(request):
    if request.method == 'POST':
        f = RecipeForm(request.POST)

        if f.is_valid():
            r = f.save(commit=False)
            r.author = request.user
            r.save()

            messages.success(request, f'"{r.name}" has been shared!')
            return redirect('recipe_detail', pk=r.pk)

    else:
        f = RecipeForm()

    return render(request, 'add_recipe.html', {'form': f})


# =========================
# DELETE RECIPE
# =========================
@login_required
def delete_recipe(request, pk):
    r = get_object_or_404(Recipe, pk=pk, author=request.user)
    r.delete()

    messages.success(request, 'Recipe deleted successfully.')
    return redirect('profile')


# =========================
# AI FUNCTION (SAFE)
# =========================
def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Indian cooking assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"


# =========================
# AI KITCHEN
# =========================
@login_required
def ai_kitchen(request):
    suggestions = []
    used = ""

    if request.method == "POST":
        used = request.POST.get("ingredients", "").strip()

        if used:
            prompt = f"""
You are a professional Indian chef AI.

User ingredients:
{used}

IMPORTANT:
Return ONLY raw JSON.
Do not use markdown.
Do not write explanation.
Do not write ```json.

Format:

[
  {{
    "name": "Paneer Curry",
    "desc": "Creamy spicy curry",
    "time": "30 mins",
    "cat": "indian"
  }}
]
"""

            try:
                text = ask_ai(prompt)

                print("AI RESPONSE:")
                print(text)

                try:
                    text = text.replace("```json", "").replace("```", "").strip()
                    suggestions = json.loads(text)

                except Exception as e:
                    print("JSON ERROR:", e)
                    print(text)

                    suggestions = [
                        {
                            "name": "AI Parsing Error",
                            "desc": text[:200],
                            "time": "",
                            "cat": "indian"
                        }
                    ]

            except Exception as e:
                suggestions = [
                    {
                        "name": "AI Error",
                        "desc": str(e),
                        "time": "",
                        "cat": "indian"
                    }
                ]

    return render(request, "ai_kitchen.html", {
        "suggestions": suggestions,
        "used": used
    })


# =========================
# CHAT PAGE
# =========================
@login_required
def chat(request):
    return render(request, 'chat.html')


# =========================
# AI CHAT API
# =========================
@login_required
def ai_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body or "{}")
        message = data.get('message')

        if not message:
            return JsonResponse({'reply': 'Empty message received.'})

        prompt = f"""
User: {message}
Reply like a friendly Indian food assistant.
"""

        reply = ask_ai(prompt)
        return JsonResponse({'reply': reply})

    return JsonResponse({'reply': 'Invalid request.'})


# =========================
# PROFILE
# =========================
@login_required
def profile(request):
    my = Recipe.objects.filter(author=request.user)
    liked = Recipe.objects.filter(likes=request.user)
    saved = Recipe.objects.filter(savedrecipe__user=request.user)

    return render(request, 'profile.html', {
        'my': my,
        'liked': liked,
        'saved': saved
    })
if not OPENROUTER_API_KEY:
    raise Exception("❌ OPENROUTER_API_KEY missing in .env file")

# =========================
# OPENROUTER CLIENT
# =========================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# =========================
# FORM
# =========================
class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'name',
            'emoji',
            'category',
            'cook_time',
            'description',
            'ingredients',
            'steps'
        ]


# =========================
# HOME
# =========================
def home(request):
    recent = Recipe.objects.all()[:6]

    top = Recipe.objects.all()
    top = sorted(top, key=lambda r: r.like_count(), reverse=True)[:3]

    total = Recipe.objects.count()

    return render(request, 'home.html', {
        'recent': recent,
        'top': top,
        'total': total
    })


# =========================
# REGISTER
# =========================
def register(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account Created!")
            return redirect('login')

    return render(request, 'register.html', {'form': form})


# =========================
# RECIPE LIST
# =========================
def recipe_list(request):
    qs = Recipe.objects.all()

    cat = request.GET.get('cat', '')
    q = request.GET.get('q', '')

    if cat:
        qs = qs.filter(category=cat)

    if q:
        qs = qs.filter(name__icontains=q)

    return render(request, 'recipe_list.html', {
        'recipes': qs,
        'cat': cat,
        'q': q,
        'categories': Recipe.CATEGORY,
    })


# =========================
# RECIPE DETAIL
# =========================
def recipe_detail(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    ings = [i.strip() for i in r.ingredients.splitlines() if i.strip()]
    steps = [s.strip() for s in r.steps.splitlines() if s.strip()]

    liked = (
        request.user.is_authenticated and
        r.likes.filter(pk=request.user.pk).exists()
    )

    saved = (
        request.user.is_authenticated and
        SavedRecipe.objects.filter(user=request.user, recipe=r).exists()
    )

    similar = Recipe.objects.filter(category=r.category or "").exclude(pk=pk)[:3]

    return render(request, 'recipe_detail.html', {
        'r': r,
        'ings': ings,
        'steps': steps,
        'liked': liked,
        'saved': saved,
        'similar': similar
    })


# =========================
# LIKE
# =========================
@login_required
def recipe_like(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    if r.likes.filter(pk=request.user.pk).exists():
        r.likes.remove(request.user)
    else:
        r.likes.add(request.user)

    return redirect('recipe_detail', pk=pk)


# =========================
# SAVE
# =========================
@login_required
def recipe_save(request, pk):
    r = get_object_or_404(Recipe, pk=pk)

    obj, created = SavedRecipe.objects.get_or_create(
        user=request.user,
        recipe=r
    )

    if not created:
        obj.delete()

    return redirect('recipe_detail', pk=pk)


# =========================
# ADD RECIPE
# =========================
@login_required
def add_recipe(request):
    if request.method == 'POST':
        f = RecipeForm(request.POST)

        if f.is_valid():
            r = f.save(commit=False)
            r.author = request.user
            r.save()

            messages.success(request, f'"{r.name}" Your Recipe Added!')
            return redirect('recipe_detail', pk=r.pk)

    else:
        f = RecipeForm()

    return render(request, 'add_recipe.html', {'form': f})


# =========================
# DELETE RECIPE
# =========================
@login_required
def delete_recipe(request, pk):
    r = get_object_or_404(Recipe, pk=pk, author=request.user)
    r.delete()

    messages.success(request, 'Recipe deleted successfully.')
    return redirect('profile')


# =========================
# AI FUNCTION (SAFE)
# =========================
def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Indian cooking assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"

# =========================
# AI KITCHEN
# =========================
@login_required
def ai_kitchen(request):

    suggestions = []
    used = ""

    if request.method == "POST":

        used = request.POST.get("ingredients", "").strip()

        if used:

            prompt = f"""
You are a professional Indian chef AI.

User ingredients:
{used}

IMPORTANT:
Return ONLY raw JSON.
Do not use markdown.
Do not write explanation.
Do not write ```json.

Format:

[
  {{
    "name": "Paneer Curry",
    "desc": "Creamy spicy curry",
    "time": "30 mins",
    "cat": "indian"
  }}
]
"""

            try:

                text = ask_ai(prompt)

                print("AI RESPONSE:")
                print(text)

                try:
                    # Remove markdown if AI adds it
                    text = text.replace("```json", "").replace("```", "").strip()

                    suggestions = json.loads(text)

                except Exception as e:

                    print("JSON ERROR:", e)
                    print(text)

                    suggestions = [
                        {
                            "name": "AI Parsing Error",
                            "desc": text[:200],
                            "time": "",
                            "cat": "indian"
                        }
                    ]

            except Exception as e:

                suggestions = [
                    {
                        "name": "AI Error",
                        "desc": str(e),
                        "time": "",
                        "cat": "indian"
                    }
                ]

    return render(request, "ai_kitchen.html", {
        "suggestions": suggestions,
        "used": used
    })


@login_required
def chat(request):
    return render(request, 'chat.html') 
# =========================
# AI CHAT API (FIXED)
# =========================
@login_required
def ai_chat(request):

    if request.method == 'POST':
        data = json.loads(request.body or "{}")
        message = data.get('message')

        if not message:
            return JsonResponse({'reply': 'Empty message'})

        prompt = f"""
User: {message}
Reply like a friendly Indian food assistant.
"""

        reply = ask_ai(prompt)

        return JsonResponse({'reply': reply})

    return JsonResponse({'reply': 'Invalid request'})


# =========================
# PROFILE
# =========================
@login_required
def profile(request):
    my = Recipe.objects.filter(author=request.user)
    liked = Recipe.objects.filter(likes=request.user)
    saved = Recipe.objects.filter(savedrecipe__user=request.user)

    return render(request, 'profile.html', {
        'my': my,
        'liked': liked,
        'saved': saved
    })