from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
Category = get_model('catalogue', 'Category')
Option = get_model('catalogue', 'Option')
Service = get_model('catalogue', 'Service')
ServiceAttribute = get_model('catalogue', 'ServiceAttribute')
ServiceAttributeValue = get_model('catalogue', 'ServiceAttributeValue')
ServiceCategory = get_model('catalogue', 'ServiceCategory')
ServiceClass = get_model('catalogue', 'ServiceClass')
ServiceImage = get_model('catalogue', 'ServiceImage')
ServiceRecommendation = get_model('catalogue', 'ServiceRecommendation')


class AttributeInline(admin.TabularInline):
    model = ServiceAttributeValue


class ServiceRecommendationInline(admin.TabularInline):
    model = ServiceRecommendation
    fk_name = 'primary'
    raw_id_fields = ['primary', 'recommendation']


class CategoryInline(admin.TabularInline):
    model = ServiceCategory
    extra = 1


class ServiceAttributeInline(admin.TabularInline):
    model = ServiceAttribute
    extra = 2


class ServiceClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_shipping', 'track_stock')
    inlines = [ServiceAttributeInline]


class ServiceAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    list_display = ('get_title', 'upc', 'get_service_class', 'structure',
                    'attribute_summary', 'date_created')
    list_filter = ['structure', 'is_discountable']
    raw_id_fields = ['parent']
    inlines = [AttributeInline, CategoryInline, ServiceRecommendationInline]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ['upc', 'title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs
            .select_related('service_class', 'parent')
            .prefetch_related(
                'attribute_values',
                'attribute_values__attribute'))


class ServiceAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'service_class', 'type')
    prepopulated_fields = {"code": ("name", )}


class OptionAdmin(admin.ModelAdmin):
    pass


class ServiceAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('service', 'attribute', 'value')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'option_summary')
    inlines = [AttributeOptionInline, ]


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ('name', 'slug')


admin.site.register(ServiceClass, ServiceClassAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceAttribute, ServiceAttributeAdmin)
admin.site.register(ServiceAttributeValue, ServiceAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(ServiceImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ServiceCategory)
