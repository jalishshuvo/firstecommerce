from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from .models import Item, Order, OrderItem, Address, Payment, Cupon, Refund
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckOutForm, CuponForm, RefundForm
from django.conf import settings

import random
import string
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits,
                                  k=20))


# Create your views here.
class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"


# def home(request):
#     template = 'home-page.html'
#     context = {'items': Item.objects.all()}
#     return render(request, template, context)


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do now have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


# def product(request):
#     template = 'product.html'
#     return render(request, template)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckOutForm()
            context = {
                'form': form,
                'order': order,
                'cuponform': CuponForm(),
                'DISPLAY_CUPON_FORM': True
            }
            return render(self.request, "checkout-page.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "you do not have an active order")
            return redirect('core: checkout')
            #form

    def post(self, *args, **kwargs):
        form = CheckOutForm(self.request.POST or None)
        # print(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                appartment_adress = form.cleaned_data.get('appartment_adress')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO : Add functionality for these fields
                # same_shipping_address = form.cleaned_data.get(
                #     'same_shipping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_options = form.cleaned_data.get('payment_options')
                billing_address = Address(user=self.request.user,
                                          street_address=street_address,
                                          appartment_adress=appartment_adress,
                                          country=country,
                                          zip=zip,
                                          address_type="B")
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # TODO:Add redirect to selected payment_options

                if payment_options == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_options == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request,
                                     "Invalid Payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, "You do now have an active order")
            return redirect('core:checkout')

            # print(form.cleaned_data)
            # print("form is valid")


class PaymentView(View):
    def get(self, *args, **kwargs):
        #order
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {'order': order, 'DISPLAY_CUPON_FORM': False}

            return render(self.request, 'payment.html', context)
        else:
            messages.warning(self.request, "You do not have a billing address")
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')

        amount = int(order.get_total() * 100)

        try:

            if use_default or save:
                # charge the customer because we cannot charge the token more than once
                charge = stripe.Charge.create(
                    amount=amount,  # cents
                    currency="usd",
                    customer=userprofile.stripe_customer_id)
            else:
                # charge once off on the token
                charge = stripe.Charge.create(
                    amount=amount,  # cents
                    currency="usd",
                    source=token)

        # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            #ref code
            order.refer_code = create_ref_code()
            order.save()

            messages.success(self.request, "Your order was successful!")
            return redirect("/")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request,
                "Something went wrong. You were not charged. Please try again."
            )
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.warning(
                self.request,
                "A serious error occurred. We have been notifed.")
            return redirect("/")


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item,
                                                          user=request.user,
                                                          ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:product", slug=slug)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user,
                                     ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:product", slug=slug)


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,
                                                  user=request.user,
                                                  ordered=False)[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():

            order_item = OrderItem.objects.filter(item=item,
                                                  user=request.user,
                                                  ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity  was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_cupon(request, code):
    try:
        cupon = Cupon.objects.get(code=code)
        return cupon
    except ObjectDoesNotExist:
        messages.info(request, "This cupon is not active")
        return redirect('core: checkout')


class AddCuponView(View):
    def post(self, *args, **kwargs):
        form = CuponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user,
                                          ordered=False)
                order.cupon = get_cupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added cupon")
                return redirect("core:checkout")

            except ObjectDoesNotExist:
                messages.info(self.request, "you do not have an active order")
                return redirect("core:checkout")
        #TO DO: raise error


class RequestRefund(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {'form': form}
        return render(self.request, 'request_refund.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            #edit the refund
            try:
                order = Order.objects.get(refer_code=ref_code)
                order.refund_requested = True
                order.save()

                #store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, "Your request was received")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")
