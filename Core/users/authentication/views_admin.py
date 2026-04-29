from datetime import timedelta
import json
import textwrap

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from exercises.models import ExerciseLog
from nutrition.models import FoodItem, MealLog
from users.models import Feedback, UserProfile


def is_admin(user):
    return user.is_staff or user.is_superuser


def format_user_rows(queryset):
    rows = []
    for user in queryset.select_related('profile').order_by('-date_joined'):
        profile = getattr(user, 'profile', None)
        rows.append({
            'username': user.username,
            'email': user.email or (profile.email if profile else ''),
            'joined': timezone.localtime(user.date_joined).strftime('%Y-%m-%d'),
            'goal': profile.get_goal_type_display() if profile and profile.goal_type else 'Not set',
            'fitness_level': profile.get_fitness_level_display() if profile and profile.fitness_level else 'Not set',
        })
    return rows


def format_food_rows(queryset):
    rows = []
    for food in queryset.order_by('name'):
        rows.append({
            'name': food.name,
            'category': food.get_category_display(),
            'source': 'Custom' if food.is_custom else food.get_source_display(),
            'calories': round(food.calories_per_100g, 1),
            'serving_unit': food.serving_unit,
            'created_by': food.created_by.username if food.created_by else '-',
        })
    return rows


def format_calorie_rows(queryset):
    totals = {}
    for log in queryset.select_related('user', 'food_item'):
        username = log.user.username
        totals.setdefault(username, 0)
        totals[username] += log.calories

    rows = [
        {
            'username': username,
            'avg_daily_calories': round(total / 30, 1),
            'total_calories': round(total, 1),
        }
        for username, total in totals.items()
    ]
    return sorted(rows, key=lambda row: row['avg_daily_calories'], reverse=True)


def _pdf_escape(text):
    return str(text).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _build_simple_pdf(title, lines):
    wrapped_lines = []
    for line in lines:
        chunks = textwrap.wrap(str(line), width=95, replace_whitespace=False, drop_whitespace=False) or ['']
        wrapped_lines.extend(chunks)

    lines_per_page = 48
    pages = [wrapped_lines[i:i + lines_per_page] for i in range(0, len(wrapped_lines), lines_per_page)] or [[]]

    objects = []

    def add_object(data):
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b'')
    pages_id = add_object(b'')
    font_id = add_object(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')

    page_ids = []
    for page_lines in pages:
        stream_lines = ['BT', '/F1 10 Tf', '50 760 Td', '14 TL']
        if not page_lines:
            stream_lines.append('( ) Tj')
        else:
            for line in page_lines:
                stream_lines.append(f'({_pdf_escape(line)}) Tj')
                stream_lines.append('T*')
        stream_lines.append('ET')
        stream = '\n'.join(stream_lines).encode('latin-1', errors='replace')
        content_id = add_object(f'<< /Length {len(stream)} >>\nstream\n'.encode('latin-1') + stream + b'\nendstream')
        page_id = add_object(
            f'<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>'.encode('latin-1')
        )
        page_ids.append(page_id)

    page_refs = ' '.join(f'{page_id} 0 R' for page_id in page_ids)
    objects[catalog_id - 1] = f'<< /Type /Catalog /Pages {pages_id} 0 R >>'.encode('latin-1')
    objects[pages_id - 1] = f'<< /Type /Pages /Kids [{page_refs}] /Count {len(page_ids)} >>'.encode('latin-1')

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{index} 0 obj\n'.encode('latin-1'))
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')

    xref_start = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('latin-1'))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode('latin-1'))

    pdf.extend(
        (
            f'trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n'
            f'startxref\n{xref_start}\n%%EOF'
        ).encode('latin-1')
    )
    return bytes(pdf)


def build_admin_dashboard_context(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)

    total_users_qs = User.objects.filter(is_staff=False)
    total_users = total_users_qs.count()

    daily_registrations = (
        total_users_qs.filter(date_joined__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    reg_labels = [r['day'].strftime('%b %d') for r in daily_registrations]
    reg_data = [r['count'] for r in daily_registrations]

    twelve_weeks_ago = today - timedelta(weeks=12)
    weekly_registrations = (
        total_users_qs.filter(date_joined__date__gte=twelve_weeks_ago)
        .annotate(week=TruncWeek('date_joined'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )
    weekly_reg_labels = [r['week'].strftime('%b %d') for r in weekly_registrations]
    weekly_reg_data = [r['count'] for r in weekly_registrations]

    twelve_months_ago = today - timedelta(days=365)
    monthly_registrations = (
        total_users_qs.filter(date_joined__date__gte=twelve_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_reg_labels = [r['month'].strftime('%b %Y') for r in monthly_registrations]
    monthly_reg_data = [r['count'] for r in monthly_registrations]

    dau_ids = list(
        ExerciseLog.objects.filter(updated_at__date=today).values_list('user_id', flat=True).distinct()
    )
    mau_ids = list(
        ExerciseLog.objects.filter(updated_at__date__gte=thirty_days_ago).values_list('user_id', flat=True).distinct()
    )

    active_user_ids = set(mau_ids)
    dau = len(set(dau_ids))
    mau = len(active_user_ids)
    active_users = len(active_user_ids)
    inactive_users = total_users - active_users

    old_users = set(
        total_users_qs.filter(date_joined__date__lte=thirty_days_ago).values_list('id', flat=True)
    )
    retained_ids = old_users & active_user_ids
    churned_ids = old_users - active_user_ids
    retained_users = len(retained_ids)
    churned_users = len(churned_ids)

    new_today_qs = total_users_qs.filter(date_joined__date=today)
    new_this_week_qs = total_users_qs.filter(date_joined__date__gte=seven_days_ago)
    new_this_month_qs = total_users_qs.filter(date_joined__date__gte=thirty_days_ago)
    active_users_qs = total_users_qs.filter(id__in=active_user_ids)
    retained_users_qs = total_users_qs.filter(id__in=retained_ids)
    churned_users_qs = total_users_qs.filter(id__in=churned_ids)

    new_today = new_today_qs.count()
    new_this_week = new_this_week_qs.count()
    new_this_month = new_this_month_qs.count()

    popular_exercises = (
        ExerciseLog.objects.values('exercise__name')
        .annotate(log_count=Count('id'))
        .order_by('-log_count')[:10]
    )
    popular_ex_labels = [e['exercise__name'] for e in popular_exercises]
    popular_ex_data = [e['log_count'] for e in popular_exercises]

    avg_workouts_per_user = round(ExerciseLog.objects.count() / max(total_users, 1), 1)

    total_logs = ExerciseLog.objects.count()
    completed_logs = sum(1 for log in ExerciseLog.objects.select_related('exercise') if log.is_completed)
    completion_rate = round((completed_logs / max(total_logs, 1)) * 100, 1)
    not_completed = round(100 - completion_rate, 1)

    category_breakdown = (
        ExerciseLog.objects.values('exercise__category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    category_labels = [c['exercise__category__name'] or 'Uncategorized' for c in category_breakdown]
    category_data = [c['count'] for c in category_breakdown]

    most_logged_foods = (
        MealLog.objects.values('food_item__name')
        .annotate(log_count=Count('id'))
        .order_by('-log_count')[:10]
    )
    food_labels = [f['food_item__name'] for f in most_logged_foods]
    food_data = [f['log_count'] for f in most_logged_foods]

    calorie_logs = MealLog.objects.filter(date__gte=thirty_days_ago).select_related('food_item', 'user')
    total_calories_logged = sum(log.calories for log in calorie_logs)
    avg_calories_per_user = round(total_calories_logged / max(active_users, 1) / 30, 0)

    custom_foods_qs = FoodItem.objects.filter(is_custom=True).select_related('created_by')
    db_foods_qs = FoodItem.objects.filter(is_custom=False).select_related('created_by')
    custom_food_count = custom_foods_qs.count()
    db_food_count = db_foods_qs.count()

    daily_calorie_labels = []
    daily_calorie_data = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        logs = MealLog.objects.filter(date=day).select_related('food_item')
        day_cal = sum(log.calories for log in logs)
        daily_calorie_labels.append(day.strftime('%b %d'))
        daily_calorie_data.append(round(day_cal, 1))

    goal_distribution = (
        UserProfile.objects.values('goal_type')
        .annotate(count=Count('user'))
        .order_by('-count')
    )
    goal_labels = [g['goal_type'].replace('_', ' ').title() for g in goal_distribution]
    goal_data = [g['count'] for g in goal_distribution]

    fitness_level_dist = (
        UserProfile.objects.values('fitness_level')
        .annotate(count=Count('user'))
        .order_by('-count')
    )
    fitness_labels = [f['fitness_level'].title() for f in fitness_level_dist]
    fitness_data = [f['count'] for f in fitness_level_dist]

    feedback_qs = Feedback.objects.select_related('user')
    recent_feedback = list(feedback_qs[:12])
    feedback_total = feedback_qs.count()
    bug_feedback_count = feedback_qs.filter(category='bug').count()
    feature_feedback_count = feedback_qs.filter(category='feature').count()
    complaint_feedback_count = feedback_qs.filter(category='complaint').count()

    user_report_details = {
        'total_users': {
            'title': 'All Users',
            'description': 'All non-staff accounts in FitTrack.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(total_users_qs),
            'empty_message': 'No users found yet.',
        },
        'new_today': {
            'title': 'New Users Today',
            'description': 'Accounts created today.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(new_today_qs),
            'empty_message': 'No new users were registered today.',
        },
        'new_this_week': {
            'title': 'New Users This Week',
            'description': 'Accounts created in the last 7 days.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(new_this_week_qs),
            'empty_message': 'No new users were registered this week.',
        },
        'new_this_month': {
            'title': 'New Users This Month',
            'description': 'Accounts created in the last 30 days.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(new_this_month_qs),
            'empty_message': 'No new users were registered this month.',
        },
        'dau': {
            'title': 'Daily Active Users',
            'description': 'Users with workout activity today.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(active_users_qs.filter(id__in=set(dau_ids))),
            'empty_message': 'No users were active today.',
        },
        'mau': {
            'title': 'Monthly Active Users',
            'description': 'Users with workout activity in the last 30 days.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(active_users_qs),
            'empty_message': 'No users were active in the last 30 days.',
        },
        'retained_users': {
            'title': 'Retained Users',
            'description': 'Users who joined over 30 days ago and returned recently.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(retained_users_qs),
            'empty_message': 'No retained users found.',
        },
        'churned_users': {
            'title': 'Churned Users',
            'description': 'Users who joined over 30 days ago and have been inactive recently.',
            'section': 'users',
            'columns': ['Username', 'Email', 'Joined', 'Goal', 'Fitness Level'],
            'rows': format_user_rows(churned_users_qs),
            'empty_message': 'No churned users found.',
        },
    }

    nutrition_report_details = {
        'avg_calories_per_user': {
            'title': 'Average Calories Per User Per Day',
            'description': 'Per-user calorie averages based on the last 30 days of meal logs.',
            'section': 'nutrition',
            'columns': ['Username', 'Avg Daily Calories', 'Total Calories'],
            'rows': format_calorie_rows(calorie_logs),
            'empty_message': 'No meal logs available yet.',
        },
        'custom_food_count': {
            'title': 'Custom Foods',
            'description': 'Foods created by users.',
            'section': 'nutrition',
            'columns': ['Name', 'Category', 'Source', 'Calories / 100g', 'Created By'],
            'rows': format_food_rows(custom_foods_qs),
            'empty_message': 'No custom foods have been created yet.',
        },
        'db_food_count': {
            'title': 'Database Foods',
            'description': 'Foods currently available from seeded or imported sources.',
            'section': 'nutrition',
            'columns': ['Name', 'Category', 'Source', 'Calories / 100g', 'Created By'],
            'rows': format_food_rows(db_foods_qs),
            'empty_message': 'No database foods found.',
        },
    }

    detail_group = request.GET.get('detail_group')
    detail_key = request.GET.get('detail_key')
    selected_detail = None
    if detail_group == 'users':
        selected_detail = user_report_details.get(detail_key)
    elif detail_group == 'nutrition':
        selected_detail = nutrition_report_details.get(detail_key)

    raw_context = {
        'today': today,
        'total_users': total_users,
        'new_today': new_today,
        'new_this_week': new_this_week,
        'new_this_month': new_this_month,
        'dau': dau,
        'mau': mau,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'retained_users': retained_users,
        'churned_users': churned_users,
        'avg_workouts_per_user': avg_workouts_per_user,
        'completion_rate': completion_rate,
        'not_completed': not_completed,
        'avg_calories_per_user': avg_calories_per_user,
        'custom_food_count': custom_food_count,
        'db_food_count': db_food_count,
        'feedback_total': feedback_total,
        'bug_feedback_count': bug_feedback_count,
        'feature_feedback_count': feature_feedback_count,
        'complaint_feedback_count': complaint_feedback_count,
        'reg_labels_raw': reg_labels,
        'reg_data_raw': reg_data,
        'weekly_reg_labels_raw': weekly_reg_labels,
        'weekly_reg_data_raw': weekly_reg_data,
        'monthly_reg_labels_raw': monthly_reg_labels,
        'monthly_reg_data_raw': monthly_reg_data,
        'popular_ex_labels_raw': popular_ex_labels,
        'popular_ex_data_raw': popular_ex_data,
        'category_labels_raw': category_labels,
        'category_data_raw': category_data,
        'food_labels_raw': food_labels,
        'food_data_raw': food_data,
        'daily_calorie_labels_raw': daily_calorie_labels,
        'daily_calorie_data_raw': daily_calorie_data,
        'goal_labels_raw': goal_labels,
        'goal_data_raw': goal_data,
        'fitness_labels_raw': fitness_labels,
        'fitness_data_raw': fitness_data,
        'user_report_details_raw': user_report_details,
        'nutrition_report_details_raw': nutrition_report_details,
        'recent_feedback_raw': [
            {
                'id': item.id,
                'user': item.user.username,
                'category': item.get_category_display(),
                'status': item.get_status_display(),
                'message': item.message,
                'admin_response': item.admin_response,
                'created_at': timezone.localtime(item.created_at).strftime('%Y-%m-%d %H:%M'),
                'responded_at': timezone.localtime(item.responded_at).strftime('%Y-%m-%d %H:%M') if item.responded_at else '',
            }
            for item in recent_feedback
        ],
    }

    template_context = {
        'today': today,
        'total_users': total_users,
        'dau': dau,
        'mau': mau,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'retained_users': retained_users,
        'churned_users': churned_users,
        'new_today': new_today,
        'new_this_week': new_this_week,
        'new_this_month': new_this_month,
        'reg_labels': json.dumps(reg_labels),
        'reg_data': json.dumps(reg_data),
        'weekly_reg_labels': json.dumps(weekly_reg_labels),
        'weekly_reg_data': json.dumps(weekly_reg_data),
        'monthly_reg_labels': json.dumps(monthly_reg_labels),
        'monthly_reg_data': json.dumps(monthly_reg_data),
        'avg_workouts_per_user': avg_workouts_per_user,
        'completion_rate': completion_rate,
        'not_completed': not_completed,
        'popular_ex_labels': json.dumps(popular_ex_labels),
        'popular_ex_data': json.dumps(popular_ex_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'avg_calories_per_user': avg_calories_per_user,
        'custom_food_count': custom_food_count,
        'db_food_count': db_food_count,
        'feedback_total': feedback_total,
        'bug_feedback_count': bug_feedback_count,
        'feature_feedback_count': feature_feedback_count,
        'complaint_feedback_count': complaint_feedback_count,
        'food_labels': json.dumps(food_labels),
        'food_data': json.dumps(food_data),
        'daily_calorie_labels': json.dumps(daily_calorie_labels),
        'daily_calorie_data': json.dumps(daily_calorie_data),
        'goal_labels': json.dumps(goal_labels),
        'goal_data': json.dumps(goal_data),
        'fitness_labels': json.dumps(fitness_labels),
        'fitness_data': json.dumps(fitness_data),
        'user_report_details': json.dumps(user_report_details),
        'nutrition_report_details': json.dumps(nutrition_report_details),
        'selected_detail': selected_detail,
        'selected_detail_group': detail_group if selected_detail else '',
        'selected_detail_key': detail_key if selected_detail else '',
        'recent_feedback': recent_feedback,
    }

    return template_context, raw_context


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_dashboard(request):
    context, _ = build_admin_dashboard_context(request)
    return render(request, 'users/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def respond_to_feedback(request, feedback_id):
    if request.method != 'POST':
        return redirect('admin_dashboard')

    feedback = get_object_or_404(Feedback, pk=feedback_id)
    admin_response = (request.POST.get('admin_response') or '').strip()
    status_value = request.POST.get('status') or feedback.status

    feedback.admin_response = admin_response
    feedback.status = status_value
    feedback.responded_at = timezone.now() if admin_response else feedback.responded_at
    feedback.save(update_fields=['admin_response', 'status', 'responded_at'])
    return redirect('admin_dashboard')


def _add_stat_block(lines, title, items):
    lines.append(title)
    lines.append('-' * len(title))
    for label, value in items:
        lines.append(f'{label}: {value}')
    lines.append('')


def _add_series_block(lines, title, labels, values):
    lines.append(title)
    lines.append('-' * len(title))
    if not labels:
        lines.append('No data available.')
    else:
        for label, value in zip(labels, values):
            lines.append(f'{label}: {value}')
    lines.append('')


def _add_table_block(lines, title, report):
    lines.append(title)
    lines.append('-' * len(title))
    lines.append(' | '.join(report['columns']))
    if not report['rows']:
        lines.append(report['empty_message'])
    else:
        for row in report['rows']:
            lines.append(' | '.join(str(value) for value in row.values()))
    lines.append('')


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def export_admin_dashboard_pdf(request):
    _, raw = build_admin_dashboard_context(request)

    lines = [
        'FitTrack Admin Dashboard Report',
        f'Generated on: {raw["today"]}',
        '',
    ]

    _add_stat_block(lines, 'User Summary', [
        ('Total Users', raw['total_users']),
        ('New Today', raw['new_today']),
        ('New This Week', raw['new_this_week']),
        ('New This Month', raw['new_this_month']),
        ('Daily Active Users', raw['dau']),
        ('Monthly Active Users', raw['mau']),
        ('Retained Users', raw['retained_users']),
        ('Churned Users', raw['churned_users']),
    ])

    _add_series_block(lines, 'Registration Growth - Daily', raw['reg_labels_raw'], raw['reg_data_raw'])
    _add_series_block(lines, 'Registration Growth - Weekly', raw['weekly_reg_labels_raw'], raw['weekly_reg_data_raw'])
    _add_series_block(lines, 'Registration Growth - Monthly', raw['monthly_reg_labels_raw'], raw['monthly_reg_data_raw'])

    _add_stat_block(lines, 'Workout Summary', [
        ('Average Workouts Per User', raw['avg_workouts_per_user']),
        ('Completion Rate', f'{raw["completion_rate"]}%'),
        ('Incomplete Rate', f'{raw["not_completed"]}%'),
    ])
    _add_series_block(lines, 'Most Popular Exercises', raw['popular_ex_labels_raw'], raw['popular_ex_data_raw'])
    _add_series_block(lines, 'Workout Category Breakdown', raw['category_labels_raw'], raw['category_data_raw'])

    _add_stat_block(lines, 'Nutrition Summary', [
        ('Average Calories Per User / Day', raw['avg_calories_per_user']),
        ('Custom Foods', raw['custom_food_count']),
        ('Database Foods', raw['db_food_count']),
    ])
    _add_series_block(lines, 'Most Logged Foods', raw['food_labels_raw'], raw['food_data_raw'])
    _add_series_block(lines, 'Daily Calorie Intake Trend', raw['daily_calorie_labels_raw'], raw['daily_calorie_data_raw'])

    _add_series_block(lines, 'Goal Distribution', raw['goal_labels_raw'], raw['goal_data_raw'])
    _add_series_block(lines, 'Fitness Level Breakdown', raw['fitness_labels_raw'], raw['fitness_data_raw'])

    _add_stat_block(lines, 'Feedback Summary', [
        ('Total Feedback Entries', raw['feedback_total']),
        ('Bug Reports', raw['bug_feedback_count']),
        ('Feature Requests', raw['feature_feedback_count']),
        ('Complaints', raw['complaint_feedback_count']),
    ])

    lines.append('Recent Feedback')
    lines.append('---------------')
    if not raw['recent_feedback_raw']:
        lines.append('No feedback has been submitted yet.')
    else:
        for item in raw['recent_feedback_raw']:
            lines.append(
                f'{item["created_at"]} | {item["user"]} | {item["category"]} | {item["status"]}'
            )
            lines.append(item['message'])
            lines.append('')

    lines.append('User Report Details')
    lines.append('-------------------')
    lines.append('')
    for report in raw['user_report_details_raw'].values():
        _add_table_block(lines, report['title'], report)

    lines.append('Nutrition Report Details')
    lines.append('------------------------')
    lines.append('')
    for report in raw['nutrition_report_details_raw'].values():
        _add_table_block(lines, report['title'], report)

    pdf_bytes = _build_simple_pdf('FitTrack Admin Dashboard Report', lines)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fittrack_admin_dashboard_report.pdf"'
    return response
