from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from plan.utils import get_budget, get_when, when_choices
from wangapi.utils import attach_bookmarks
from .models import Eventful


def eventful_home_view(request):
    amount, show_all = get_budget(request)
    when, start, end = get_when(request)

    view_all_events = request.GET.get('all') == '1'

    if when and not request.GET.get('amount', '').strip():
        show_all = True

    today = timezone.localdate()
    events = Eventful.objects.all()
    events = events.filter(
            Q(one_time=False) | Q(event_date__isnull=True) | Q(event_date__gte=today)
        )

    if not view_all_events:

        if when:
            events = events.filter(event_date__range=(start, end))
        if not show_all:
            events = events.filter(price__lte=amount)

    results = [{'pk': e.pk,
                'kind': e._meta.label_lower,
                'name': e.name,
                'price': e.price,
                'place': e.location,
                'description': e.description,
                'one_time': e.one_time,
                'event_date': e.event_date,
                'image': e.image,
                'instagram': e.instagram,
                'twitter': e.twitter,
                'tiktok': e.tiktok,
                'website': e.website,
                'tickets': e.tickets,
                'change': amount - e.price} for e in events]

    if when:
        results.sort(key=lambda r: (r['event_date'], r['price']))
    else:
        results.sort(key=lambda r: r['price'] if show_all else r['change'])
    attach_bookmarks(request.user, results)

    choices = when_choices()
    when_label = ''
    if when == 'date':
        when_label = start.strftime('%a %d %b %Y')
    elif when:
        when_label = dict(choices).get(when, '')

    return render(request, 'eventful/home.html', {
        'amount': amount,
        'show_all': show_all,
        'results': results,
        'when': when,
        'when_choices': choices,
        'when_label': when_label,
        'date_value': start.isoformat() if when == 'date' else '',
    })