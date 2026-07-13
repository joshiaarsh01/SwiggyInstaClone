from django.shortcuts import render, get_object_or_404, redirect
from .models import Brand, Product, ProductVariant, Order, OrderLineItem, Customer, Godown, ProductStock, VariantStock
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib import messages
import hashlib, secrets, math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Returns distance in kilometers between two GPS points."""
    R = 6371
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_nearest_godown(lat, lon):
    """Returns (nearest_godown, distance_km) or (None, None) if no godowns exist."""
    nearest = None
    min_dist = None
    for godown in Godown.objects.all():
        dist = haversine_distance(lat, lon, godown.latitude, godown.longitude)
        if min_dist is None or dist < min_dist:
            min_dist = dist
            nearest = godown
    return nearest, min_dist

def get_available_stock(request, item_type, item_id, fallback_obj=None):
    """Returns stock quantity for an item at the session's nearest godown, or falls back to the old single stock field."""
    godown_id = request.session.get('nearest_godown_id')
    if godown_id:
        if item_type == 'product':
            stock_row = ProductStock.objects.filter(godown_id=godown_id, product_id=item_id).first()
        else:
            stock_row = VariantStock.objects.filter(godown_id=godown_id, variant_id=item_id).first()
        return stock_row.quantity if stock_row else 0
    elif fallback_obj:
        return fallback_obj.stock
    return 0

def home(request):
    query = request.GET.get('q', '').strip()

    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if lat and lon:
        request.session['customer_lat'] = float(lat)
        request.session['customer_lon'] = float(lon)
        nearest, dist = get_nearest_godown(float(lat), float(lon))
        if nearest:
            request.session['nearest_godown_id'] = nearest.id
            request.session['nearest_godown_name'] = nearest.godown_name
        return redirect('home')

    has_location = bool(request.session.get('nearest_godown_id'))

    if query:
        brands = Brand.objects.filter(b_name__icontains=query)
        products = Product.objects.filter(p_name__icontains=query).select_related('b').prefetch_related('variants')
    else:
        brands = Brand.objects.all()
        products = Product.objects.select_related('b').prefetch_related('variants').all()

    product_data = []
    for product in products:
        variants = list(product.variants.all())

        if variants:
            prices = [v.price for v in variants]
            stock_total = sum(v.stock for v in variants)
            low_price = min(prices)
            high_price = max(prices)
            price_display = f"{low_price}" if low_price == high_price else f"{low_price}–{high_price}"
            img = variants[0].variant_img if variants[0].variant_img else product.p_img
        else:
            stock_total = product.stock
            price_display = product.p_price
            img = product.p_img

        product_data.append({
            'product': product,
            'price_display': price_display,
            'stock_total': stock_total,
            'has_variants': bool(variants),
            'img': img,
        })

    return render(request, 'store/home.html', {
        'brands': brands,
        'product_data': product_data,
        'query': query,
        'has_location': has_location,
    })
    
def brand_products(request, brand_id):
    brand = get_object_or_404(Brand, b_id=brand_id)
    products = Product.objects.filter(b=brand)
    return render(request, 'store/brand_products.html', {'brand': brand, 'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, p_id=product_id)
    variants = product.variants.all()
    wishlist = request.session.get('wishlist', [])

    godown_id = request.session.get('nearest_godown_id')
    godown_name = request.session.get('nearest_godown_name')

    if godown_id:
        stock_row = ProductStock.objects.filter(godown_id=godown_id, product=product).first()
        product_stock = stock_row.quantity if stock_row else 0

        for v in variants:
            vs_row = VariantStock.objects.filter(godown_id=godown_id, variant=v).first()
            v.godown_stock = vs_row.quantity if vs_row else 0
    else:
        product_stock = product.stock
        for v in variants:
            v.godown_stock = v.stock

    return render(request, 'store/product_detail.html', {
        'product': product, 'variants': variants, 'wishlist': wishlist,
        'product_stock': product_stock, 'godown_name': godown_name,
    })

def add_to_cart(request, item_type, item_id):
    cart = request.session.get('cart', {})
    key = f"{item_type}-{item_id}"

    if item_type == 'product':
        obj = Product.objects.filter(p_id=item_id).first()
    else:
        obj = ProductVariant.objects.filter(id=item_id).first()
    available = obj.stock if obj else 0

    requested_qty = int(request.GET.get('qty', 1))
    current_qty = cart.get(key, 0)

    new_qty = current_qty + requested_qty
    if new_qty > available:
        new_qty = available

    cart[key] = new_qty
    request.session['cart'] = cart

    wishlist = request.session.get('wishlist', [])
    if key in wishlist:
        wishlist.remove(key)
        request.session['wishlist'] = wishlist

    return redirect('cart')


def increase_qty(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        item_type, item_id = key.split('-')
        if item_type == 'product':
            obj = Product.objects.filter(p_id=item_id).first()
        else:
            obj = ProductVariant.objects.filter(id=item_id).first()
        available = obj.stock if obj else 0

        if cart[key] < available:
            cart[key] += 1
    request.session['cart'] = cart
    return redirect('cart')


def cart_view(request):
    if not request.session.get('customer_id'):
        messages.error(request, 'Please log in to view your cart.')
        return redirect('login')

    cart = request.session.get('cart', {})
    items = []
    total = 0
    for key, qty in list(cart.items()):
        if '-' not in key or qty <= 0:
            if key in cart:
                del cart[key]
            continue
        item_type, item_id = key.split('-')

        if item_type == 'product':
            product = Product.objects.filter(p_id=item_id).first()
            if product:
                available = product.stock
                if qty > available:
                    qty = available
                    cart[key] = qty
                price = product.p_price or 0
                subtotal = price * qty
                total += subtotal
                stock_by_godown = [
                    {'name': g.godown_name, 'qty': (ProductStock.objects.filter(godown=g, product=product).first().quantity if ProductStock.objects.filter(godown=g, product=product).exists() else 0)}
                    for g in Godown.objects.all()
                ]
                items.append({
                    'key': key, 'name': product.p_name, 'img': product.p_img,
                    'price': price, 'qty': qty, 'subtotal': subtotal,
                    'stock_by_godown': stock_by_godown
                })
        elif item_type == 'variant':
            variant = ProductVariant.objects.filter(id=item_id).first()
            if variant:
                available = variant.stock
                if qty > available:
                    qty = available
                    cart[key] = qty
                subtotal = variant.price * qty
                total += subtotal
                stock_by_godown = [
                    {'name': g.godown_name, 'qty': (VariantStock.objects.filter(godown=g, variant=variant).first().quantity if VariantStock.objects.filter(godown=g, variant=variant).exists() else 0)}
                    for g in Godown.objects.all()
                ]
                items.append({
                    'key': key, 'name':variant.variant_name,
                    'img': variant.variant_img, 'price': variant.price, 'qty': qty, 'subtotal': subtotal,
                    'stock_by_godown': stock_by_godown
                })
        elif item_type == 'variant':
            variant = ProductVariant.objects.filter(id=item_id).first()
            if variant:
                if qty > variant.stock:
                    qty = variant.stock
                    cart[key] = qty
                subtotal = variant.price * qty
                total += subtotal
                items.append({
                    'key': key, 'name':variant.variant_name,
                    'img': variant.variant_img, 'price': variant.price, 'qty': qty, 'subtotal': subtotal
                })
    request.session['cart'] = cart

    any_godown_covers_all = False
    for godown in Godown.objects.all():
        covers_all = True
        for item in items:
            item_godown_stock = next((gs['qty'] for gs in item['stock_by_godown'] if gs['name'] == godown.godown_name), 0)
            if item['qty'] > item_godown_stock:
                covers_all = False
                break
        if covers_all:
            any_godown_covers_all = True
            break

    can_order = bool(items) and any_godown_covers_all

    return render(request, 'store/cart.html', {'items': items, 'total': total, 'can_order': can_order})

def remove_from_cart(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
    request.session['cart'] = cart
    return redirect('cart')

def decrease_qty(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
    request.session['cart'] = cart
    return redirect('cart')

def clear_cart(request):
    request.session['cart'] = {}
    return redirect('cart')

def add_to_wishlist(request, item_type, item_id):
    wishlist = request.session.get('wishlist', [])
    key = f"{item_type}-{item_id}"
    if key not in wishlist:
        wishlist.append(key)
    request.session['wishlist'] = wishlist
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def remove_from_wishlist(request, key):
    wishlist = request.session.get('wishlist', [])
    if key in wishlist:
        wishlist.remove(key)
    request.session['wishlist'] = wishlist
    return redirect('wishlist')

def wishlist_view(request):
    wishlist = request.session.get('wishlist', [])
    items = []
    for key in wishlist:
        if '-' not in key:
            continue
        item_type, item_id = key.split('-')
        if item_type == 'product':
            product = Product.objects.filter(p_id=item_id).first()
            if product:
                items.append({
                    'key': key, 'name': product.p_name, 'img': product.p_img,
                    'price': product.p_price, 'item_type': item_type, 'item_id': item_id,
                    'stock': get_available_stock(request, item_type, item_id, fallback_obj=product)
                })
        elif item_type == 'variant':
            variant = ProductVariant.objects.filter(id=item_id).first()
            if variant:
                items.append({
                    'key': key, 'name': variant.variant_name, 'img': variant.variant_img,
                    'price': variant.price, 'item_type': item_type, 'item_id': item_id,
                    'stock': get_available_stock(request, item_type, item_id, fallback_obj=variant)
                })
    return render(request, 'store/wishlist.html', {'items': items})

def toggle_wishlist(request, item_type, item_id):
    wishlist = request.session.get('wishlist', [])
    key = f"{item_type}-{item_id}"
    if key in wishlist:
        wishlist.remove(key)
        added = False
    else:
        wishlist.append(key)
        added = True
    request.session['wishlist'] = wishlist
    return JsonResponse({'added': added})

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')

    items = []
    total = 0
    for key, qty in cart.items():
        if '-' not in key:
            continue
        item_type, item_id = key.split('-')
        if item_type == 'product':
            product = Product.objects.filter(p_id=item_id).first()
            if product:
                price = product.p_price or 0
                subtotal = price * qty
                total += subtotal
                items.append({
                    'name': product.p_name, 'price': price, 'qty': qty,
                    'subtotal': subtotal, 'img': product.p_img,
                    'item_type': 'product', 'item_id': product.p_id
                })
        elif item_type == 'variant':
            variant = ProductVariant.objects.filter(id=item_id).first()
            if variant:
                subtotal = variant.price * qty
                total += subtotal
                items.append({
                    'name': variant.variant_name, 'price': variant.price, 'qty': qty,
                    'subtotal': subtotal, 'img': variant.variant_img,
                    'item_type': 'variant', 'item_id': variant.id
                })

    customer_id = request.session.get('customer_id')
    customer = Customer.objects.filter(c_id=customer_id).first() if customer_id else None

    checkout_lat = request.session.get('customer_lat')
    checkout_lon = request.session.get('customer_lon')
    has_location = bool(checkout_lat and checkout_lon)

    godown_options = []
    if has_location:
        for godown in Godown.objects.all():
            dist = haversine_distance(checkout_lat, checkout_lon, godown.latitude, godown.longitude)

            all_available = True
            for item in items:
                if item['item_type'] == 'product':
                    stock_row = ProductStock.objects.filter(godown=godown, product_id=item['item_id']).first()
                else:
                    stock_row = VariantStock.objects.filter(godown=godown, variant_id=item['item_id']).first()
                available_qty = stock_row.quantity if stock_row else 0
                if item['qty'] > available_qty:
                    all_available = False
                    break

            godown_options.append({
                'id': godown.id,
                'name': godown.godown_name,
                'area': godown.area,
                'distance': round(dist, 1),
                'charge': round(dist * 5),
                'all_available': all_available,
            })
        godown_options.sort(key=lambda g: g['distance'])

    if request.method == 'POST':
        name = request.POST.get('name')
        number = request.POST.get('number')
        same_location = request.POST.get('same_location')
        selected_godown_id = request.POST.get('godown_id')

        delivery_charge = 0
        delivery_godown = None
        delivery_latitude = None
        delivery_longitude = None

        if selected_godown_id:
            delivery_godown = Godown.objects.filter(id=selected_godown_id).first()
            if delivery_godown and has_location:
                dist = haversine_distance(checkout_lat, checkout_lon, delivery_godown.latitude, delivery_godown.longitude)
                delivery_charge = round(dist * 5)

        if delivery_godown:
            for item in items:
                if item['item_type'] == 'product':
                    stock_row = ProductStock.objects.filter(godown=delivery_godown, product_id=item['item_id']).first()
                else:
                    stock_row = VariantStock.objects.filter(godown=delivery_godown, variant_id=item['item_id']).first()
                available = stock_row.quantity if stock_row else 0
                if item['qty'] > available:
                    messages.error(
                        request,
                        f"{item['name']} — only {available} available at {delivery_godown.godown_name}. Please pick a different godown or reduce quantity."
                    )
                    return render(request, 'store/checkout.html', {
                        'items': items, 'total': total,
                        'has_location': has_location, 'godown_options': godown_options,
                        'customer': customer,
                    })

        if same_location == 'yes' and has_location:
            address = f"Current GPS Location ({checkout_lat}, {checkout_lon})"
            delivery_latitude = checkout_lat
            delivery_longitude = checkout_lon
        else:
            address = request.POST.get('address')

        order = Order.objects.create(
            customer_name=name,
            customer_number=number,
            delivery_address=address,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            delivery_godown=delivery_godown,
            delivery_charge=delivery_charge,
            total_amount=total + delivery_charge,
            status='Placed'
        )
        for item in items:
            OrderLineItem.objects.create(
                order=order,
                item_name=item['name'],
                price=item['price'],
                quantity=item['qty'],
                img_url=item['img'].url if item['img'] else ''
            )

            if delivery_godown:
                if item['item_type'] == 'product':
                    stock_row = ProductStock.objects.filter(godown=delivery_godown, product_id=item['item_id']).first()
                else:
                    stock_row = VariantStock.objects.filter(godown=delivery_godown, variant_id=item['item_id']).first()
                if stock_row:
                    stock_row.quantity -= item['qty']
                    stock_row.save()

        request.session['cart'] = {}

        if customer and customer.c_email:
            item_lines = '\n'.join(
                [f"- {item['name']} x {item['qty']} — ₹{item['subtotal']}" for item in items]
            )
            send_mail(
                f'Order Confirmed — #{order.id}',
                f"Hi {name},\n\nYour order has been placed successfully!\n\n"
                f"Order #{order.id}\n\n{item_lines}\n\nDelivery charge: ₹{delivery_charge}\n\n"
                f"Total: ₹{total + delivery_charge}\n\n"
                f"Delivery Address:\n{address}\n\nThank you for shopping with SwiggyInstaClone!",
                None,
                [customer.c_email],
            )

        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'items': items, 'total': total,
        'has_location': has_location, 'godown_options': godown_options,
        'customer': customer,
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    return render(request, 'store/order_confirmation.html', {'order': order, 'items': items})

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        number = request.POST.get('number')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if Customer.objects.filter(c_email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'store/register.html')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        customer = Customer.objects.create(
            a_id=1,
            c_name=name,
            c_number=number,
            c_email=email,
            c_password=hashed_password,
            is_active=False,
        )

        otp = str(secrets.randbelow(900000) + 100000)
        request.session[f'otp_{customer.c_id}'] = otp

        send_mail(
            'Your SwiggyInstaClone OTP',
            f'Hi {name},\n\nYour OTP for account verification is: {otp}\n\nEnter this on the website to verify your account.',
            None,
            [email],
        )

        return redirect('verify_otp', customer_id=customer.c_id)

    return render(request, 'store/register.html')


def verify_otp(request, customer_id):
    customer = get_object_or_404(Customer, c_id=customer_id)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        expected_otp = request.session.get(f'otp_{customer_id}')

        if entered_otp == expected_otp:
            customer.is_active = True
            customer.save()

            request.session.pop(f'otp_{customer_id}', None)
            request.session['customer_id'] = customer.c_id
            request.session['customer_name'] = customer.c_name

            return redirect('home')
        else:
            messages.error(request, 'Incorrect OTP. Please try again.')

    return render(request, 'store/verify_otp.html', {'email': customer.c_email})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        customer = Customer.objects.filter(c_email=email, c_password=hashed_password).first()

        if not customer:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'store/login.html')

        if not customer.is_active:
            messages.error(request, 'Please verify your email before logging in.')
            return render(request, 'store/login.html')

        request.session['customer_id'] = customer.c_id
        request.session['customer_name'] = customer.c_name
        request.session['cart'] = {}
        request.session['wishlist'] = []
        return redirect('home')

    return render(request, 'store/login.html')


def logout_view(request):
    request.session.pop('customer_id', None)
    request.session.pop('customer_name', None)
    request.session.pop('cart', None)
    request.session.pop('wishlist', None)
    return redirect('home')