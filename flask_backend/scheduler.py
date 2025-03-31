from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from .models import db, Task, RecurrenceRule

def check_recurring_tasks():
    """Check for tasks that need to be recurred and create new instances."""
    with db.app.app_context():
        # Get all tasks with active recurrence rules
        recurring_tasks = Task.query.filter(
            Task.recurrence_rule != RecurrenceRule.NONE,
            (Task.recurrence_end.is_(None) | (Task.recurrence_end > datetime.utcnow()))
        ).all()
        
        for task in recurring_tasks:
            # Get the latest instance of this recurring task
            latest_instance = Task.query.filter_by(original_task_id=task.id).order_by(Task.created_at.desc()).first()
            reference_task = latest_instance if latest_instance else task
            
            # Create next instance if needed
            next_task = reference_task.create_next_recurrence()
            if next_task:
                db.session.add(next_task)
        
        db.session.commit()

def init_scheduler(app):
    """Initialize the task scheduler."""
    scheduler = BackgroundScheduler()
    
    # Schedule the recurring task check to run daily at midnight
    scheduler.add_job(
        check_recurring_tasks,
        CronTrigger(hour=0, minute=0),
        id='check_recurring_tasks',
        name='Check and create recurring tasks',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler 