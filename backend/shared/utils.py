# shared/utils.py

from datetime import datetime, timezone

def current_timestamp():
    """Return current timestamp in epoch format"""
    return int(datetime.now(timezone.utc).timestamp())

def validate_epoch_timestamp(timestamp):
    """Validate that timestamp is a valid epoch timestamp"""
    try:
        if isinstance(timestamp, (int, float)):
            return timestamp > 0
        return False
    except (ValueError, TypeError):
        return False

def validate_status(status, allowed_statuses):
    """Validate status against allowed values"""
    return status.lower() in [s.lower() for s in allowed_statuses]

def format_deadline(deadline_epoch):
    """Format deadline epoch to readable date"""
    dt = datetime.fromtimestamp(deadline_epoch, tz=timezone.utc)
    return dt.strftime("%B %d, %Y at %I:%M %p UTC")

def days_until_deadline(deadline_epoch):
    """Calculate days until deadline from current time"""
    current_time = current_timestamp()
    seconds_until_deadline = deadline_epoch - current_time
    days = seconds_until_deadline / (24 * 60 * 60)
    return round(days, 1)