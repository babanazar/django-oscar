# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, FormView, ListView, UpdateView, View)

from oscar.core.loading import get_class, get_model
from oscar.core.utils import redirect_to_referrer, safe_referrer

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')
Service = get_model('catalogue', 'Service')
WishListForm = get_class('wishlists.forms', 'WishListForm')
LineFormset = get_class('wishlists.formsets', 'LineFormset')
PageTitleMixin = get_class('customer.mixins', 'PageTitleMixin')


class WishListListView(PageTitleMixin, ListView):
    context_object_name = active_tab = "wishlists"
    template_name = 'oscar/customer/wishlists/wishlists_list.html'
    page_title = _('Wish Lists')

    def get_queryset(self):
        """
        Return a list of all the wishlists for the currently
        authenticated user.
        """
        return self.request.user.wishlists.all()


class WishListDetailView(PageTitleMixin, FormView):
    """
    This view acts as a DetailView for a wish list and allows updating the
    quantities of services.

    It is implemented as FormView because it's easier to adapt a FormView to
    display a service then adapt a DetailView to handle form validation.
    """
    template_name = 'oscar/customer/wishlists/wishlists_detail.html'
    active_tab = "wishlists"
    form_class = LineFormset

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_wishlist_or_404(kwargs['key'], request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_wishlist_or_404(self, key, user):
        wishlist = get_object_or_404(WishList, key=key)
        if wishlist.is_allowed_to_see(user):
            return wishlist
        else:
            raise Http404

    def get_page_title(self):
        return self.object.name

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wishlist'] = self.object
        other_wishlists = self.request.user.wishlists.exclude(
            pk=self.object.pk)
        ctx['other_wishlists'] = other_wishlists
        return ctx

    def form_valid(self, form):
        for subform in form:
            if subform.cleaned_data['quantity'] <= 0:
                subform.instance.delete()
            else:
                subform.save()
        messages.success(self.request, _('Quantities updated.'))
        return redirect('customer:wishlists-detail', key=self.object.key)


class WishListCreateView(PageTitleMixin, CreateView):
    """
    Create a new wishlist

    If a service ID is passed as a kwargs, then this service will be added to
    the wishlist.
    """
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    page_title = _('Create a new wish list')
    form_class = WishListForm
    service = None

    def dispatch(self, request, *args, **kwargs):
        if 'service_pk' in kwargs:
            try:
                self.service = Service.objects.get(pk=kwargs['service_pk'])
            except ObjectDoesNotExist:
                messages.error(
                    request, _("The requested service no longer exists"))
                return redirect('wishlists-create')
        return super().dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['service'] = self.service
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        wishlist = form.save()
        if self.service:
            wishlist.add(self.service)
            msg = _("Your wishlist has been created and '%(name)s "
                    "has been added") \
                % {'name': self.service.get_title()}
        else:
            msg = _("Your wishlist has been created")
        messages.success(self.request, msg)
        return redirect(wishlist.get_absolute_url())


class WishListCreateWithServiceView(View):
    """
    Create a wish list and immediately add a service to it
    """

    def post(self, request, *args, **kwargs):
        service = get_object_or_404(Service, pk=kwargs['service_pk'])
        wishlists = request.user.wishlists.all()
        if len(wishlists) == 0:
            wishlist = request.user.wishlists.create()
        else:
            # This shouldn't really happen but we default to using the first
            # wishlist for a user if one already exists when they make this
            # request.
            wishlist = wishlists[0]
        wishlist.add(service)
        messages.success(
            request, _("%(title)s has been added to your wishlist") % {
                'title': service.get_title()})
        return redirect_to_referrer(request, wishlist.get_absolute_url())


class WishListUpdateView(PageTitleMixin, UpdateView):
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    form_class = WishListForm
    context_object_name = 'wishlist'

    def get_page_title(self):
        return self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(
            self.request, _("Your '%s' wishlist has been updated")
            % self.object.name)
        return reverse('customer:wishlists-list')


class WishListDeleteView(PageTitleMixin, DeleteView):
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_delete.html'
    active_tab = "wishlists"

    def get_page_title(self):
        return _('Delete %s') % self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_success_url(self):
        messages.success(
            self.request, _("Your '%s' wish list has been deleted")
            % self.object.name)
        return reverse('customer:wishlists-list')


class WishListAddService(View):
    """
    Adds a service to a wish list.

    - If the user doesn't already have a wishlist then it will be created for
      them.
    - If the service is already in the wish list, its quantity is increased.
    """

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, pk=kwargs['service_pk'])
        self.wishlist = self.get_or_create_wishlist(request, *args, **kwargs)
        return super().dispatch(request)

    def get_or_create_wishlist(self, request, *args, **kwargs):
        if 'key' in kwargs:
            wishlist = get_object_or_404(
                WishList, key=kwargs['key'], owner=request.user)
        else:
            wishlists = request.user.wishlists.all()[:1]
            if not wishlists:
                return request.user.wishlists.create()
            wishlist = wishlists[0]

        if not wishlist.is_allowed_to_edit(request.user):
            raise PermissionDenied
        return wishlist

    def get(self, request, *args, **kwargs):
        # This is nasty as we shouldn't be performing write operations on a GET
        # request.  It's only included as the UI of the service detail page
        # allows a wishlist to be selected from a dropdown.
        return self.add_service()

    def post(self, request, *args, **kwargs):
        return self.add_service()

    def add_service(self):
        self.wishlist.add(self.service)
        msg = _("'%s' was added to your wish list.") % self.service.get_title()
        messages.success(self.request, msg)
        return redirect_to_referrer(
            self.request, self.service.get_absolute_url())


class LineMixin(object):
    """
    Handles fetching both a wish list and a service
    Views using this mixin must be passed two keyword arguments:

    * key: The key of a wish list
    * line_pk: The primary key of the wish list line

    or

    * service_pk: The primary key of the service
    """

    def fetch_line(self, user, wishlist_key, line_pk=None, service_pk=None):
        if line_pk is not None:
            self.line = get_object_or_404(
                Line,
                pk=line_pk,
                wishlist__owner=user,
                wishlist__key=wishlist_key,
            )
        else:
            try:
                self.line = get_object_or_404(
                    Line,
                    service_id=service_pk,
                    wishlist__owner=user,
                    wishlist__key=wishlist_key,
                )
            except Line.MultipleObjectsReturned:
                raise Http404
        self.wishlist = self.line.wishlist
        self.service = self.line.service


class WishListRemoveService(LineMixin, PageTitleMixin, DeleteView):
    template_name = 'oscar/customer/wishlists/wishlists_delete_service.html'
    active_tab = "wishlists"

    def get_page_title(self):
        return _('Remove %s') % self.object.get_title()

    def get_object(self, queryset=None):
        self.fetch_line(
            self.request.user,
            self.kwargs['key'],
            self.kwargs.get('line_pk'),
            self.kwargs.get('service_pk')
        )
        return self.line

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wishlist'] = self.wishlist
        ctx['service'] = self.service
        return ctx

    def get_success_url(self):
        msg = _("'%(title)s' was removed from your '%(name)s' wish list") % {
            'title': self.line.get_title(),
            'name': self.wishlist.name}
        messages.success(self.request, msg)

        # We post directly to this view on service pages; and should send the
        # user back there if that was the case
        referrer = safe_referrer(self.request, '')
        if (referrer and self.service
                and self.service.get_absolute_url() in referrer):
            return referrer
        else:
            return reverse(
                'customer:wishlists-detail', kwargs={'key': self.wishlist.key})


class WishListMoveServiceToAnotherWishList(LineMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.fetch_line(request.user, kwargs['key'], line_pk=kwargs['line_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        to_wishlist = get_object_or_404(
            WishList, owner=request.user, key=kwargs['to_key'])

        if to_wishlist.lines.filter(service=self.line.service).count() > 0:
            msg = _("Wish list '%(name)s' already containing '%(title)s'") % {
                'title': self.service.get_title(),
                'name': to_wishlist.name}
            messages.error(self.request, msg)
        else:
            self.line.wishlist = to_wishlist
            self.line.save()

            msg = _("'%(title)s' moved to '%(name)s' wishlist") % {
                'title': self.service.get_title(),
                'name': to_wishlist.name}
            messages.success(self.request, msg)

        default_url = reverse(
            'customer:wishlists-detail', kwargs={'key': self.wishlist.key})
        return redirect_to_referrer(self.request, default_url)
