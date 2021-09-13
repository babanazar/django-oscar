from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, View

from oscar.apps.catalogue.reviews.signals import review_added
from oscar.core.loading import get_classes, get_model
from oscar.core.utils import redirect_to_referrer

ServiceReviewForm, VoteForm, SortReviewsForm = get_classes(
    'catalogue.reviews.forms',
    ['ServiceReviewForm', 'VoteForm', 'SortReviewsForm'])

Vote = get_model('reviews', 'vote')
ServiceReview = get_model('reviews', 'ServiceReview')
Service = get_model('catalogue', 'service')


class CreateServiceReview(CreateView):
    template_name = "oscar/catalogue/reviews/review_form.html"
    model = ServiceReview
    service_model = Service
    form_class = ServiceReviewForm
    view_signal = review_added

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(
            self.service_model, pk=kwargs['service_pk'], is_public=True)
        # check permission to leave review
        if not self.service.is_review_permitted(request.user):
            if self.service.has_review_by(request.user):
                message = _("You have already reviewed this service!")
            else:
                message = _("You can't leave a review for this service.")
            messages.warning(self.request, message)
            return redirect(self.service.get_absolute_url())

        return super().dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['service'] = self.service
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.send_signal(self.request, response, self.object)
        return response

    def get_success_url(self):
        messages.success(
            self.request, _("Thank you for reviewing this service"))
        return self.service.get_absolute_url()

    def send_signal(self, request, response, review):
        self.view_signal.send(sender=self, review=review, user=request.user,
                              request=request, response=response)


class ServiceReviewDetail(DetailView):
    template_name = "oscar/catalogue/reviews/review_detail.html"
    context_object_name = 'review'
    model = ServiceReview

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(
            Service, pk=self.kwargs['service_pk'], is_public=True)
        return context


class AddVoteView(View):
    """
    Simple view for voting on a review.

    We use the URL path to determine the service and review and use a 'delta'
    POST variable to indicate it the vote is up or down.
    """

    def post(self, request, *args, **kwargs):
        service = get_object_or_404(Service, pk=self.kwargs['service_pk'], is_public=True)
        review = get_object_or_404(ServiceReview, pk=self.kwargs['pk'])

        form = VoteForm(review, request.user, request.POST)
        if form.is_valid():
            if form.is_up_vote:
                review.vote_up(request.user)
            elif form.is_down_vote:
                review.vote_down(request.user)
            messages.success(request, _("Thanks for voting!"))
        else:
            for error_list in form.errors.values():
                for msg in error_list:
                    messages.error(request, msg)
        return redirect_to_referrer(request, service.get_absolute_url())


class ServiceReviewList(ListView):
    """
    Browse reviews for a service
    """
    template_name = 'oscar/catalogue/reviews/review_list.html'
    context_object_name = "reviews"
    model = ServiceReview
    service_model = Service
    paginate_by = settings.OSCAR_REVIEWS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.approved().filter(service=self.kwargs['service_pk'])
        self.form = SortReviewsForm(self.request.GET)
        if self.request.GET and self.form.is_valid():
            sort_by = self.form.cleaned_data['sort_by']
            if sort_by == SortReviewsForm.SORT_BY_RECENCY:
                return qs.order_by('-date_created')
        return qs.order_by('-score')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(
            self.service_model, pk=self.kwargs['service_pk'], is_public=True)
        context['form'] = self.form
        return context
