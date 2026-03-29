from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = [
    ('staples', 'Staples'),
    ('proteins', 'Proteins'),
    ('vegetables', 'Vegetables'),
    ('fruits', 'Fruits'),
    ('snacks', 'Snacks'),
    ('drinks', 'Drinks'),
]

MEAL_TYPE_CHOICES = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
    ('snack', 'Snack'),
]


class FoodItem(models.Model):
    SOURCE_CHOICES = [
        ('local','kenyan_food_fixture'),
        ('usda','USDA'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    serving_unit = models.CharField(max_length=20, default='g')
    default_serving_size = models.FloatField(default=100)
    calories_per_100g = models.FloatField()
    protein_per_100g = models.FloatField()
    carbs_per_100g = models.FloatField()
    fats_per_100g = models.FloatField()
    fiber_per_100g = models.FloatField(default=0)
    description = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='local')
    usda_fdc_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together=('name','source')

    def __str__(self):
        return self.name

    def nutrition_for_portion(self, portion_grams):
        factor = portion_grams / 100
        return {
            'calories': round(self.calories_per_100g * factor, 1),
            'protein': round(self.protein_per_100g * factor, 1),
            'carbs': round(self.carbs_per_100g * factor, 1),
            'fats': round(self.fats_per_100g * factor, 1),
            'fiber': round(self.fiber_per_100g * factor, 1),
        }


class MealLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_logs')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    portion_size = models.FloatField(default=100, help_text='Portion in grams')
    protein_portion = models.FloatField(default=0, help_text='Protein in grams')
    carbs_portion = models.FloatField(default=0, help_text='Carbs in grams ')
    fats_portion = models.FloatField(default=0, help_text='fats iin grams')
    notes = models.CharField(max_length=200, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-logged_at']

    def __str__(self):
        return f"{self.user.username} - {self.food_item.name} on {self.date}"
    
    def save(self, *args, **kwargs):
        factor = self.portion_size / 100
        self.protein_portion = round(self.food_item.protein_per_100g * factor, 1)
        self.carbs_portion = round(self.food_item.carbs_per_100g * factor, 1)
        self.fats_portion = round(self.food_item.fats_per_100g * factor, 1)
        super().save(*args, **kwargs)

    @property
    def calories(self):
        return round(self.food_item.calories_per_100g * self.portion_size / 100, 1)

    @property
    def protein(self):
        return round(self.food_item.protein_per_100g * self.portion_size / 100, 1)

    @property
    def carbs(self):
        return round(self.food_item.carbs_per_100g * self.portion_size / 100, 1)

    @property
    def fats(self):
        return round(self.food_item.fats_per_100g * self.portion_size / 100, 1)