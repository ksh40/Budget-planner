from django.shortcuts import render
from decimal import Decimal, InvalidOperation

def home_view(request):
    raw_amount = request.GET.get('amount','')
    try:
        amount = Decimal(raw_amount)
    except(InvalidOperation, TypeError):
        amount = Decimal('0.00')
    context = {
        'amount': amount,
    }
        
    return render (request, 'plan/home.html', context)
