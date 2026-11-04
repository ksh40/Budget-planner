
from django.shortcuts import render, get_object_or_404

from food.models import Item, Bundle
from activities.models import Activity
from eventful.models import Eventful
from punguza.models import Punguza
from students.models import Students

def share_post_view(request, mode, post_type, pk):
    if mode == 'food' and post_type == 'item':
        post = get_object_or_404(Item, pk=pk)
        title = post.name
        place = post.place
        image = post.image

    elif mode == 'food' and post_type == 'bundle':
        post = get_object_or_404(Bundle, pk=pk)
        title = post.title
        place = ''
        image = post.image

    elif mode == 'activities' and post_type == 'activity':
        post = get_object_or_404(Activity, pk=pk)
        title = post.name
        place = post.location
        image = post.image

    elif mode == 'events' and post_type == 'event':
        post = get_object_or_404(Eventful, pk=pk)
        title = post.name
        place = post.location
        image = post.image
    
    elif mode == 'punguza' and post_type == 'punguza':
        post = get_object_or_404(Punguza, pk=pk)
        title = post.name
        place = post.place
        image = post.image

    elif mode == 'students' and post_type == 'students':
        post = get_object_or_404(Students, pk=pk)
        title = post.name
        place = post.location
        image = post.image

    else:
        from django.http import Http404
        raise Http404('Post not found')

    description = f'{title} — KSh {post.price}'
    if place:
        description += f' at {place}'

    image_url = (
        request.build_absolute_uri(image.url)
        if image
        else request.build_absolute_uri('/static/plan/images/ukopreview.jpg')
    )


    share_url = request.build_absolute_uri()


    destination = {
        'food': '/food/',
        'activities': '/activities/',
        'events': '/eventful/',
        'punguza': '/punguza/',
        'students': '/students/',
    }[mode]

    destination_url = (
        request.build_absolute_uri(destination)
        + f'?all=1#post-{post._meta.label_lower}-{post.pk}'
    )

    return render(request, 'wangapi/share_post.html', {
        'title': title,
        'description': description,
        'image_url': image_url,
        'share_url': share_url,
        'destination_url': destination_url,
    })
