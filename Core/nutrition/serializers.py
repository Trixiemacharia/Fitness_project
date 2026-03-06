from rest_framework import serializers
from .models import FoodItem, MealLog


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'category', 'serving_unit',
            'default_serving_size', 'calories_per_100g',
            'protein_per_100g', 'carbs_per_100g',
            'fats_per_100g', 'fiber_per_100g', 'description'
        ]


class MealLogSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food_item.name', read_only=True)
    food_category = serializers.CharField(source='food_item.category', read_only=True)
    serving_unit = serializers.CharField(source='food_item.serving_unit', read_only=True)
    calories = serializers.FloatField(read_only=True)
    protein = serializers.FloatField(read_only=True)
    carbs = serializers.FloatField(read_only=True)
    fats = serializers.FloatField(read_only=True)

    class Meta:
        model = MealLog
        fields = [
            'id', 'food_item', 'food_name', 'food_category',
            'date', 'meal_type', 'portion_size', 'serving_unit',
            'notes', 'logged_at',
            'calories', 'protein', 'carbs', 'fats'
        ]
        read_only_fields = ['user', 'logged_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DailySummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_calories = serializers.FloatField()
    total_protein = serializers.FloatField()
    total_carbs = serializers.FloatField()
    total_fats = serializers.FloatField()
    meal_count = serializers.IntegerField()
    meals_by_type = serializers.DictField()