from datetime import timedelta

from django import template

register = template.Library()


@register.filter
def duration(value):
    """Format a timedelta (or seconds) as H:MM:SS / M:SS."""
    if value in (None, ''):
        return '—'
    seconds = int(value.total_seconds() if isinstance(value, timedelta) else value)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes}:{secs:02d}'


@register.filter
def performance(value, exercise):
    """Format a best-set value according to the exercise metric."""
    if value is None:
        return '—'
    if exercise.metric_type == exercise.METRIC_TIME:
        return duration(value)
    if exercise.metric_type == exercise.METRIC_WEIGHTED:
        return f'{value:+g} kg'
    return f'{int(value)} reps'


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """Current GET params with some keys replaced — keeps filters when paginating."""
    params = context['request'].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()
