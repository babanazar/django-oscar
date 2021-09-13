from django.urls import reverse_lazy

from oscar.forms.widgets import MultipleRemoteSelect, RemoteSelect


class ServiceSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-service-lookup')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['class'] = 'select2 service-select'


class ServiceSelectMultiple(MultipleRemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-service-lookup')
