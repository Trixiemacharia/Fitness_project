from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FoodItem, MealLog
from .serializers import FoodItemSerializer, MealLogSerializer


class FoodSearchView(generics.ListAPIView):
    #Search food items by name, returns matching results.
    serializer_class = FoodItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return FoodItem.objects.none()
        return FoodItem.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )[:20]


class MealLogListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/nutrition/logs/?date=2024-01-15  — list logs for a date
    POST /api/nutrition/logs/                   — create a new log entry
    """
    serializer_class = MealLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        date = self.request.query_params.get('date', timezone.now().date())
        return MealLog.objects.filter(
            user=self.request.user,
            date=date
        ).select_related('food_item')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MealLogDeleteView(generics.DestroyAPIView):
    #DELETE /api/nutrition/logs/<pk>/
    serializer_class = MealLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealLog.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_summary(request):
    #Return total macros for the day.
    date = request.query_params.get('date', timezone.now().date())
    logs = MealLog.objects.filter(user=request.user, date=date).select_related('food_item')

    total_calories = sum(log.calories for log in logs)
    total_protein = sum(log.protein for log in logs)
    total_carbs = sum(log.carbs for log in logs)
    total_fats = sum(log.fats for log in logs)

    meals_by_type = {}
    for meal_type, label in MealLog._meta.get_field('meal_type').choices:
        type_logs = [log for log in logs if log.meal_type == meal_type]
        meals_by_type[meal_type] = {
            'label': label,
            'count': len(type_logs),
            'calories': round(sum(log.calories for log in type_logs), 1),
        }

    return Response({
        'date': date,
        'total_calories': round(total_calories, 1),
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fats': round(total_fats, 1),
        'meal_count': logs.count(),
        'meals_by_type': meals_by_type,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_summary(request):
    #Returns last 7 days of calorie data for chart.js chart.
    from datetime import timedelta, date
    today = timezone.now().date()
    days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        logs = MealLog.objects.filter(user=request.user, date=day).select_related('food_item')
        days.append({
            'date': str(day),
            'day_label': day.strftime('%a'),
            'calories': round(sum(log.calories for log in logs), 1),
            'protein': round(sum(log.protein for log in logs), 1),
            'carbs': round(sum(log.carbs for log in logs), 1),
            'fats': round(sum(log.fats for log in logs), 1),
        })
    return Response(days)