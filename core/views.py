from django.shortcuts import render
from events.models import Event
from django.db.models import Q


def home_view(request):
    matched_events = []
    other_events = []

    all_events = Event.objects.filter(status='approved')

    if request.user.is_authenticated:
        try:
            interests = request.user.profile.interests
            location = request.user.profile.location
        except:
            interests = ''
            location = ''

        if interests or location:
            query = Q()

            if interests:
                interest_list = [i.strip() for i in interests.split(',')]
                for interest in interest_list:
                    query |= Q(category__icontains=interest) | Q(title__icontains=interest)

            if location:
                query |= Q(location__icontains=location)

            matched_events = all_events.filter(query)
            matched_ids = matched_events.values_list('id', flat=True)
            other_events = all_events.exclude(id__in=matched_ids)[:6]
        else:
            other_events = all_events[:6]
    else:
        other_events = all_events[:6]

    context = {
        'matched_events': matched_events,
        'other_events': other_events,
    }
    return render(request, 'core/homepage.html', context)