from django import forms
from django.core import exceptions
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_classes, get_model

Service = get_model('catalogue', 'Service')
ServiceClass = get_model('catalogue', 'ServiceClass')
ServiceAttribute = get_model('catalogue', 'ServiceAttribute')
StockRecord = get_model('partner', 'StockRecord')
ServiceCategory = get_model('catalogue', 'ServiceCategory')
ServiceImage = get_model('catalogue', 'ServiceImage')
ServiceRecommendation = get_model('catalogue', 'ServiceRecommendation')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

(StockRecordForm,
 ServiceCategoryForm,
 ServiceImageForm,
 ServiceRecommendationForm,
 ServiceAttributesForm,
 AttributeOptionForm) = \
    get_classes('dashboard.catalogue.forms',
                ('StockRecordForm',
                 'ServiceCategoryForm',
                 'ServiceImageForm',
                 'ServiceRecommendationForm',
                 'ServiceAttributesForm',
                 'AttributeOptionForm'))


BaseStockRecordFormSet = inlineformset_factory(
    Service, StockRecord, form=StockRecordForm, extra=1)


class StockRecordFormSet(BaseStockRecordFormSet):

    def __init__(self, service_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not user.is_staff
        self.service_class = service_class

        if not user.is_staff and \
           'instance' in kwargs and \
           'queryset' not in kwargs:
            kwargs.update({
                'queryset': StockRecord.objects.filter(service=kwargs['instance'],
                                                       partner__in=user.partners.all())
            })

        super().__init__(*args, **kwargs)
        self.set_initial_data()

    def set_initial_data(self):
        """
        If user has only one partner associated, set the first
        stock record's partner to it. Can't pre-select for staff users as
        they're allowed to save a service without a stock record.

        This is intentionally done after calling __init__ as passing initial
        data to __init__ creates a form for each list item. So depending on
        whether we can pre-select the partner or not, we'd end up with 1 or 2
        forms for an unbound form.
        """
        if self.require_user_stockrecord:
            try:
                user_partner = self.user.partners.get()
            except (exceptions.ObjectDoesNotExist,
                    exceptions.MultipleObjectsReturned):
                pass
            else:
                partner_field = self.forms[0].fields.get('partner', None)
                if partner_field and partner_field.initial is None:
                    partner_field.initial = user_partner

    def _construct_form(self, i, **kwargs):
        kwargs['service_class'] = self.service_class
        kwargs['user'] = self.user
        return super()._construct_form(
            i, **kwargs)

    def clean(self):
        """
        If the user isn't a staff user, this validation ensures that at least
        one stock record's partner is associated with a users partners.
        """
        if any(self.errors):
            return
        if self.require_user_stockrecord:
            stockrecord_partners = set([form.cleaned_data.get('partner', None)
                                        for form in self.forms])
            user_partners = set(self.user.partners.all())
            if not user_partners & stockrecord_partners:
                raise exceptions.ValidationError(
                    _("At least one stock record must be set to a partner that"
                      " you're associated with."))


BaseServiceCategoryFormSet = inlineformset_factory(
    Service, ServiceCategory, form=ServiceCategoryForm, extra=1,
    can_delete=True)


class ServiceCategoryFormSet(BaseServiceCategoryFormSet):

    def __init__(self, service_class, user, *args, **kwargs):
        # This function just exists to drop the extra arguments
        super().__init__(*args, **kwargs)

    def clean(self):
        if not self.instance.is_child and self.get_num_categories() == 0:
            raise forms.ValidationError(
                _("Stand-alone and parent services "
                  "must have at least one category"))
        if self.instance.is_child and self.get_num_categories() > 0:
            raise forms.ValidationError(
                _("A child service should not have categories"))

    def get_num_categories(self):
        num_categories = 0
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if (hasattr(form, 'cleaned_data')
                    and form.cleaned_data.get('category', None)
                    and not form.cleaned_data.get('DELETE', False)):
                num_categories += 1
        return num_categories


BaseServiceImageFormSet = inlineformset_factory(
    Service, ServiceImage, form=ServiceImageForm, extra=2)


class ServiceImageFormSet(BaseServiceImageFormSet):

    def __init__(self, service_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseServiceRecommendationFormSet = inlineformset_factory(
    Service, ServiceRecommendation, form=ServiceRecommendationForm,
    extra=5, fk_name="primary")


class ServiceRecommendationFormSet(BaseServiceRecommendationFormSet):

    def __init__(self, service_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


ServiceAttributesFormSet = inlineformset_factory(ServiceClass,
                                                 ServiceAttribute,
                                                 form=ServiceAttributesForm,
                                                 extra=3)


AttributeOptionFormSet = inlineformset_factory(AttributeOptionGroup,
                                               AttributeOption,
                                               form=AttributeOptionForm,
                                               extra=3)
