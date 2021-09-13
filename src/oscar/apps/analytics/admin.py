from django.contrib import admin

from oscar.core.loading import get_model


class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('service', 'num_views', 'num_basket_additions',
                    'num_purchases')


class UserServiceViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'date_created')


class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_service_views', 'num_basket_additions',
                    'num_orders', 'total_spent', 'date_last_order')


admin.site.register(get_model('analytics', 'servicerecord'),
                    ServiceRecordAdmin)
admin.site.register(get_model('analytics', 'userrecord'), UserRecordAdmin)
admin.site.register(get_model('analytics', 'usersearch'))
admin.site.register(get_model('analytics', 'userserviceview'),
                    UserServiceViewAdmin)
