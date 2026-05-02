from datetime import timedelta
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FoodItem, MealLog
from .serializers import FoodItemSerializer, MealLogSerializer
from services.meal_plan_service import generate_meal_plan
from services.nutrition_service import calculate_targets
from users.models import MealPlan


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def food_search(request):
    query = request.query_params.get('q','').strip()
    if not query or len(query)<2:
        return Response([])
    from services.food_service import search_food
    results = search_food(query)
    return Response(results)


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

#meal plan 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_meal_plan(request):
    try:
        profile = request.user.profile

        if not profile.wants_meal_plan:
            return Response(
                {'error':'Meal plan not requested'},
                status= status.HTTP_400_BAD_REQUEST
            )
        meal_plan = generate_meal_plan(request.user)
        targets = calculate_targets(profile)
        return Response({
            'success': True,
            'meal_plan_id': meal_plan.id,
            'name': meal_plan.name,
            'daily_targets': targets,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_meal_plan(request):
    """Fetch the user's active meal plan"""
    try:
        meal_plan = MealPlan.objects.get(user=request.user, is_active=True)
        days_data = {}

        for day in meal_plan.days.all():
            days_data[day.day] = {
                'breakfast': [],
                'lunch': [],
                'dinner': [],
                'snack': [],
            }
            for item in day.items.select_related('food'):
                days_data[day.day][item.meal_type].append({
                    'food': item.food.name,
                    'quantity': item.quantity,
                    'unit': item.quantity_unit,
                    'calories': item.calories,
                    'protein': item.protein,
                    'carbs': item.carbs, 
                    'fats': item.fats,       
                })

        return Response({
            'meal_plan': meal_plan.name,
            'goal': meal_plan.goal,
            'daily_targets': {
                'calories': meal_plan.target_calories,
                'protein': meal_plan.target_protein,
                'carbs': meal_plan.target_carbs,
                'fats': meal_plan.target_fat,   
            },
            'days': days_data,
        })

    except MealPlan.DoesNotExist:
        return Response(
            {'error': 'No active meal plan found'},
            status=status.HTTP_404_NOT_FOUND
        )