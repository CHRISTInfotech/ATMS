from django import template

register = template.Library()

@register.filter
def format_duration(value):
    """
    Works for both timedelta (Task.total_time) and seconds (int, SubTask.time_spent_seconds)
    """
    if not value:
        return "0s"

    # Convert seconds to timedelta if value is int
    if isinstance(value, int):
        total_seconds = value
    else:
        total_seconds = int(value.total_seconds())

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
