from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import DetailView
from pos.models import Menu, Order
from pos.forms import MenuForm, OrderForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from pos.task import slack_notification
from core.settings import LOGGER
from django.shortcuts import redirect


class IndexView(LoginRequiredMixin, ListView):
    context_object_name = "latest_menu_list"

    def get_queryset(self):
        return Menu.objects.order_by("created_at")


class OrderCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Order
    form_class = OrderForm
    # success_url = reverse_lazy("pos:index")
    success_message = "Order was created successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["menu"] = Menu.objects.get(pk=self.kwargs["menu_id"])
        return context

    def form_valid(self, form):
        form.instance.menu = Menu.objects.get(pk=self.kwargs["menu_id"])
        super(OrderCreateView, self).form_valid(form)
        return redirect(
            reverse_lazy("pos:detail", kwargs={"pk": self.kwargs["menu_id"]})
        )

    def get_success_url(self) -> str:
        return reverse_lazy("pos:detail", kwargs={"pk": self.kwargs["menu_id"]})


class CreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Menu
    form_class = MenuForm
    success_url = reverse_lazy("pos:index")
    success_message = "Menu was created successfully"

    def post(self, request):
        response = super(CreateView, self).post(request)

        try:
            slack_notification.delay(self.object.id)
            messages.info(request, "A notification has been sent to all users")
        except Exception as error:
            messages.error(request, error)
            LOGGER.error(error)

        return response


class DetailView(DetailView):
    model = Menu

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["order"] = Order.objects.filter(
            user=self.request.user, menu=self.kwargs["pk"]
        ).first()
        return context


class UpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Menu
    form_class = MenuForm
    success_url = reverse_lazy("pos:index")
    success_message = "Menu was updated successfully"


class DeleteView(LoginRequiredMixin, DeleteView):
    model = Menu
    success_url = reverse_lazy("pos:index")