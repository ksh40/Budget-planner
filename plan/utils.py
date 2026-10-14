from decimal import Decimal, InvalidOperation


def get_budget(request):
    try:
        amount = Decimal(request.GET.get('amount', ''))
        if not amount.is_finite() or amount < 0:
            amount = Decimal('0.00')
    except (InvalidOperation, TypeError):
        amount = Decimal('0.00')
    show_all = request.GET.get('all') == '1'
    return amount, show_all