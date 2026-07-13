def auth_status(request):
    return {
        'is_logged_in': bool(request.session.get('customer_id')),
        'customer_name': request.session.get('customer_name', ''),
    }