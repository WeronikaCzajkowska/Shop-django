from django.urls import reverse
from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Order

def order_create(request):
    cart = Cart(request)
    form = OrderCreateForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                        product=item['product'],
                                        price=item['price'],
                                        quantity=item['quantity'])
            # Usunięcie zawartości koszyka na zakupy.
            cart.clear()
            # Uruchomienie zadania asynchronicznego.
            order_created.delay(order.id)
            # Umieszczenie zamówienia w sesji.
            request.session['order_id'] = order.id
            # Przekierowanie do płatności.
            return redirect(reverse('payment:process'))
        else:
            form = OrderCreateForm()
    return render(request,'orders/order/create.html',{'cart': cart, 'form': form})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request,
                'admin/orders/order/detail.html',
                {'order': order})