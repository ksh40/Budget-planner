from plan.utils import get_budget
from django.shortcuts import render
from .models import Students
from wangapi.utils import attach_bookmarks

def students_home_view(request):
    amount, show_all = get_budget(request)
    students = Students.objects.all() if show_all else Students.objects.filter(price__lte=amount)

    results = [{'pk': s.pk,
                'kind': s._meta.label_lower,
                'name': s.name, 
                'price': s.price,
                'og_price': s.og_price, 
                'savings': s.savings,
                'discount': s.discount,
                'percent_off': s.percent_off,
                'discount_note': s.discount_note,
                'place': s.location,
                'description': s.description,
                'image': s.image, 
                'website':s.website,
                'change': amount - s.price} for s in students]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])
    attach_bookmarks(request.user, results)

    return render(request, 'students/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })
    