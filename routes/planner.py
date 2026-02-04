"""
Study Planner Routes - Task and study session management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from models.database import Task

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')


@planner_bp.route('/')
@login_required
def index():
    """View study planner"""
    today = date.today()
    
    # Get tasks for different views
    today_tasks = current_user.tasks.filter(Task.due_date == today).order_by(Task.priority.desc()).all()
    upcoming_tasks = current_user.tasks.filter(
        Task.due_date > today,
        Task.status == 'pending'
    ).order_by(Task.due_date).limit(10).all()
    
    # Calculate productivity stats
    week_start = today - timedelta(days=today.weekday())
    week_tasks = current_user.tasks.filter(
        Task.due_date >= week_start,
        Task.due_date <= today
    ).all()
    
    completed_this_week = sum(1 for t in week_tasks if t.is_completed)
    total_this_week = len(week_tasks)
    completion_rate = round((completed_this_week / total_this_week * 100) if total_this_week > 0 else 0)
    
    # Study hours this week
    study_hours = sum(t.actual_hours or 0 for t in week_tasks if t.is_completed)
    
    return render_template('planner.html',
                         today=today,
                         today_tasks=today_tasks,
                         upcoming_tasks=upcoming_tasks,
                         completed_this_week=completed_this_week,
                         total_this_week=total_this_week,
                         completion_rate=completion_rate,
                         study_hours=study_hours,
                         categories=Task.CATEGORIES)


@planner_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    """Add a new task"""
    if request.method == 'POST':
        try:
            due_date = None
            due_time = None
            
            if request.form.get('due_date'):
                due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
            if request.form.get('due_time'):
                due_time = datetime.strptime(request.form['due_time'], '%H:%M').time()
            
            new_task = Task(
                user_id=current_user.id,
                title=request.form['title'].strip(),
                description=request.form.get('description', '').strip(),
                due_date=due_date,
                due_time=due_time,
                priority=request.form.get('priority', 'medium'),
                category=request.form.get('category'),
                estimated_hours=float(request.form['estimated_hours']) if request.form.get('estimated_hours') else None
            )
            
            db.session.add(new_task)
            db.session.commit()
            
            flash(f'Task "{new_task.title}" added! ✅', 'success')
            return redirect(url_for('planner.index'))
            
        except Exception as e:
            flash(f'Error adding task: {str(e)}', 'error')
    
    return render_template('task_form.html',
                         task=None,
                         categories=Task.CATEGORIES)


@planner_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    """Edit an existing task"""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            if request.form.get('due_date'):
                task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
            if request.form.get('due_time'):
                task.due_time = datetime.strptime(request.form['due_time'], '%H:%M').time()
            
            task.title = request.form['title'].strip()
            task.description = request.form.get('description', '').strip()
            task.priority = request.form.get('priority', 'medium')
            task.category = request.form.get('category')
            
            if request.form.get('estimated_hours'):
                task.estimated_hours = float(request.form['estimated_hours'])
            
            db.session.commit()
            
            flash(f'Task "{task.title}" updated! ✅', 'success')
            return redirect(url_for('planner.index'))
            
        except Exception as e:
            flash(f'Error updating task: {str(e)}', 'error')
    
    return render_template('task_form.html',
                         task=task,
                         categories=Task.CATEGORIES)


@planner_bp.route('/complete/<int:id>', methods=['POST'])
@login_required
def complete_task(id):
    """Mark task as completed"""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    actual_hours = request.form.get('actual_hours')
    if actual_hours:
        task.actual_hours = float(actual_hours)
    
    task.complete()
    db.session.commit()
    
    flash(f'Task "{task.title}" completed! 🎉', 'success')
    return redirect(url_for('planner.index'))


@planner_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    """Delete a task"""
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted 🗑️', 'success')
    return redirect(url_for('planner.index'))


@planner_bp.route('/weekly')
@login_required
def weekly_view():
    """Weekly planner view"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get tasks for the week
    week_tasks = current_user.tasks.filter(
        Task.due_date >= week_start,
        Task.due_date <= week_end
    ).order_by(Task.due_date, Task.priority.desc()).all()
    
    # Organize by day
    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_tasks = [t for t in week_tasks if t.due_date == day_date]
        days.append({
            'date': day_date,
            'name': day_date.strftime('%A'),
            'tasks': day_tasks,
            'is_today': day_date == today
        })
    
    return render_template('planner_weekly.html',
                         days=days,
                         week_start=week_start,
                         week_end=week_end)


@planner_bp.route('/stats')
@login_required
def stats():
    """Productivity statistics"""
    today = date.today()
    
    # This month's stats
    month_start = today.replace(day=1)
    month_tasks = current_user.tasks.filter(
        Task.due_date >= month_start
    ).all()
    
    completed = sum(1 for t in month_tasks if t.is_completed)
    total_hours = sum(t.actual_hours or 0 for t in month_tasks if t.is_completed)
    
    # Category breakdown
    categories = {}
    for task in month_tasks:
        cat = task.category or 'other'
        if cat not in categories:
            categories[cat] = {'total': 0, 'completed': 0}
        categories[cat]['total'] += 1
        if task.is_completed:
            categories[cat]['completed'] += 1
    
    return render_template('planner_stats.html',
                         month_tasks=len(month_tasks),
                         completed=completed,
                         total_hours=total_hours,
                         categories=categories)


@planner_bp.route('/api/today')
@login_required
def api_today():
    """API endpoint for today's tasks"""
    today_tasks = current_user.tasks.filter(Task.due_date == date.today()).all()
    
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'category': t.category,
        'priority': t.priority,
        'is_completed': t.is_completed,
        'estimated_hours': t.estimated_hours
    } for t in today_tasks])
