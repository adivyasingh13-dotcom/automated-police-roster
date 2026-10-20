from app.models import db, Notification

def create_notification(user_id: int, title: str, message: str, category: str = "GENERAL") -> Notification:
    """Helper to create an in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        is_read=False
    )
    db.session.add(notif)
    db.session.commit()
    return notif
