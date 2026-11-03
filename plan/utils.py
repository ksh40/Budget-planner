from decimal import Decimal, InvalidOperation
import calendar
import re
from datetime import date, timedelta
from django.utils import timezone

def get_budget(request):
    try:
        amount = Decimal(request.GET.get('amount', ''))
        if not amount.is_finite() or amount < 0:
            amount = Decimal('0.00')
    except (InvalidOperation, TypeError):
        amount = Decimal('0.00')
    show_all = request.GET.get('all') == '1'
    return amount, show_all

_MONTH_KEY = re.compile(r'^(\d{4})-(\d{2})$')


def _month_end(first):
    return first.replace(day=calendar.monthrange(first.year, first.month)[1])


def when_choices(today=None):
    """Dropdown options for the optional date filter."""
    today = today or timezone.localdate()
    choices = [
        ('', 'Any time'),
        ('today', 'Today'),
        ('tomorrow', 'Tomorrow'),
        ('next_week', 'Next week'),
    ]
    for i in range(12):
        index = today.month - 1 + i
        year, month = today.year + index // 12, index % 12 + 1
        label = calendar.month_name[month] + (f' {year}' if year != today.year else '')
        choices.append((f'{year}-{month:02d}', label))
    return choices


def resolve_when(key, raw_date, today):
    """Turn the chosen option into (key, start, end). ('', None, None) means no date filter."""
    raw_date = (raw_date or '').strip()
    if raw_date:
        try:
            chosen = date.fromisoformat(raw_date)
            return 'date', chosen, chosen
        except ValueError:
            pass

    if key == 'today':
        return key, today, today
    if key == 'tomorrow':
        tomorrow = today + timedelta(days=1)
        return key, tomorrow, tomorrow
    if key == 'next_week':
        start = today + timedelta(days=7 - today.weekday()) 
        return key, start, start + timedelta(days=6)

    match = _MONTH_KEY.match(key or '')
    if match:
        try:
            first = date(int(match.group(1)), int(match.group(2)), 1)
        except ValueError:
            return '', None, None
        return key, max(first, today), _month_end(first)

    return '', None, None


def get_when(request):
    """Read the optional date filter from the URL."""
    return resolve_when(request.GET.get('when', ''), request.GET.get('date', ''), timezone.localdate())