from urllib.parse import quote

from django.contrib import messages
from django.core.paginator import InvalidPage
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from oscar.apps.catalogue.signals import service_viewed
from oscar.core.loading import get_class, get_model

Service = get_model('catalogue', 'service')
Category = get_model('catalogue', 'category')
ServiceAlert = get_model('customer', 'ServiceAlert')
ServiceAlertForm = get_class('customer.forms', 'ServiceAlertForm')
get_service_search_handler_class = get_class(
    'catalogue.search_handlers', 'get_service_search_handler_class')


class ServiceDetailView(DetailView):
    context_object_name = 'service'
    model = Service
    view_signal = service_viewed
    template_folder = "catalogue"

    # Whether to redirect to the URL with the right path
    enforce_paths = True

    # Whether to redirect child services to their parent's URL. If it's disabled,
    # we display variant service details on the separate page. Otherwise, details
    # displayed on parent service page.
    enforce_parent = False

    def get(self, request, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        self.object = service = self.get_object()

        redirect = self.redirect_if_necessary(request.path, service)
        if redirect is not None:
            return redirect

        # Do allow staff members so they can test layout etc.
        if not self.is_viewable(service, request):
            raise Http404()

        response = super().get(request, **kwargs)
        self.send_signal(request, response, service)
        return response

    def is_viewable(self, service, request):
        return service.is_public or request.user.is_staff

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, 'object'):
            return self.object
        else:
            return super().get_object(queryset)

    def redirect_if_necessary(self, current_path, service):
        if self.enforce_parent and service.is_child:
            return HttpResponsePermanentRedirect(
                service.parent.get_absolute_url())

        if self.enforce_paths:
            expected_path = service.get_absolute_url()
            if expected_path != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['alert_form'] = self.get_alert_form()
        ctx['has_active_alert'] = self.get_alert_status()
        return ctx

    def get_alert_status(self):
        # Check if this user already have an alert for this service
        has_alert = False
        if self.request.user.is_authenticated:
            alerts = ServiceAlert.objects.filter(
                service=self.object, user=self.request.user,
                status=ServiceAlert.ACTIVE)
            has_alert = alerts.exists()
        return has_alert

    def get_alert_form(self):
        return ServiceAlertForm(
            user=self.request.user, service=self.object)

    def send_signal(self, request, response, service):
        self.view_signal.send(
            sender=self, service=service, user=request.user, request=request,
            response=response)

    def get_template_names(self):
        """
        Return a list of possible templates.

        If an overriding class sets a template name, we use that. Otherwise,
        we try 2 options before defaulting to :file:`catalogue/detail.html`:

            1. :file:`detail-for-upc-{upc}.html`
            2. :file:`detail-for-class-{classname}.html`

        This allows alternative templates to be provided for a per-service
        and a per-item-class basis.
        """
        if self.template_name:
            return [self.template_name]

        return [
            'oscar/%s/detail-for-upc-%s.html' % (
                self.template_folder, self.object.upc),
            'oscar/%s/detail-for-class-%s.html' % (
                self.template_folder, self.object.get_service_class().slug),
            'oscar/%s/detail.html' % self.template_folder]


class CatalogueView(TemplateView):
    """
    Browse all services in the catalogue
    """
    context_object_name = "services"
    template_name = 'oscar/catalogue/browse.html'

    def get(self, request, *args, **kwargs):
        try:
            self.search_handler = self.get_search_handler(
                self.request.GET, request.get_full_path(), [])
        except InvalidPage:
            # Redirect to page one.
            messages.error(request, _('The given page number was invalid.'))
            return redirect('catalogue:index')
        return super().get(request, *args, **kwargs)

    def get_search_handler(self, *args, **kwargs):
        return get_service_search_handler_class()(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = {}
        ctx['summary'] = _("All services")
        search_context = self.search_handler.get_search_context_data(
            self.context_object_name)
        ctx.update(search_context)
        return ctx


class ServiceCategoryView(TemplateView):
    """
    Browse services in a given category
    """
    context_object_name = "services"
    template_name = 'oscar/catalogue/category.html'
    enforce_paths = True

    def get(self, request, *args, **kwargs):
        # Fetch the category; return 404 or redirect as needed
        self.category = self.get_category()

        # Allow staff members so they can test layout etc.
        if not self.is_viewable(self.category, request):
            raise Http404()

        potential_redirect = self.redirect_if_necessary(
            request.path, self.category)
        if potential_redirect is not None:
            return potential_redirect

        try:
            self.search_handler = self.get_search_handler(
                request.GET, request.get_full_path(), self.get_categories())
        except InvalidPage:
            messages.error(request, _('The given page number was invalid.'))
            return redirect(self.category.get_absolute_url())

        return super().get(request, *args, **kwargs)

    def is_viewable(self, category, request):
        return category.is_public or request.user.is_staff

    def get_category(self):
        return get_object_or_404(Category, pk=self.kwargs['pk'])

    def redirect_if_necessary(self, current_path, category):
        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has changed, issue a redirect.
            expected_path = category.get_absolute_url()
            if expected_path != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_search_handler(self, *args, **kwargs):
        return get_service_search_handler_class()(*args, **kwargs)

    def get_categories(self):
        """
        Return a list of the current category and its ancestors
        """
        return self.category.get_descendants_and_self()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        search_context = self.search_handler.get_search_context_data(
            self.context_object_name)
        context.update(search_context)
        return context
