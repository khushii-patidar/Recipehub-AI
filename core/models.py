from django.db import models
from django.contrib.auth.models import User

class Recipe(models.Model):
    CATEGORY = [
        ('indian','🇮🇳 Indian'), ('italian','🍕 Italian'),
        ('dessert','🍰 Dessert'), ('healthy','🥗 Healthy'),
        ('street','🍜 Street Food'), ('other','🍽️ Other'),
    ]
    author      = models.ForeignKey(User, on_delete=models.CASCADE)
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ingredients = models.TextField(help_text="Write each ingredient on a separate line")
    steps       = models.TextField(help_text="Write each step on a separate line")
    category    = models.CharField(max_length=20, choices=CATEGORY, default='other')
    cook_time   = models.CharField(max_length=50, blank=True)
    emoji       = models.CharField(max_length=10, default='🍽️')
    likes       = models.ManyToManyField(User, related_name='liked', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def like_count(self):
        return self.likes.count()

class SavedRecipe(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user','recipe')
