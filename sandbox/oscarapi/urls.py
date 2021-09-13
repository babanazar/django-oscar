# pylint: disable=unbalanced-tuple-unpacking
from django.conf import settings
from django.urls import include, path, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from oscarapi.utils.loading import get_api_classes, get_api_class

api_root = get_api_class("views.root", "api_root")
(LoginView, UserDetail, RegistrationView) = get_api_classes(
    "views.login", ["LoginView", "UserDetail", "RegistrationView"]
)
(
    BasketView,
    AddServiceView,
    AddVoucherView,
    ShippingMethodView,
    LineList,
    BasketLineDetail,
) = get_api_classes(
    "views.basket",
    [
        "BasketView",
        "AddServiceView",
        "AddVoucherView",
        "ShippingMethodView",
        "LineList",
        "BasketLineDetail",
    ],
)

(StockRecordDetail, PartnerList, PartnerDetail) = get_api_classes(
    "views.admin.partner", ["StockRecordDetail", "PartnerList", "PartnerDetail"]
)

(
    BasketList,
    BasketDetail,
    LineAttributeDetail,
    OptionList,
    OptionDetail,
    CountryList,
    CountryDetail,
    RangeList,
    RangeDetail,
) = get_api_classes(
    "views.basic",
    [
        "BasketList",
        "BasketDetail",
        "LineAttributeDetail",
        "OptionList",
        "OptionDetail",
        "CountryList",
        "CountryDetail",
        "RangeList",
        "RangeDetail",
    ],
)

(
    ServiceList,
    ServiceDetail,
    ServiceStockRecords,
    ServiceStockRecordDetail,
    ServicePrice,
    ServiceAvailability,
    CategoryList,
    CategoryDetail,
) = get_api_classes(
    "views.service",
    [
        "ServiceList",
        "ServiceDetail",
        "ServiceStockRecords",
        "ServiceStockRecordDetail",
        "ServicePrice",
        "ServiceAvailability",
        "CategoryList",
        "CategoryDetail",
    ],
)

(
    CheckoutView,
    OrderList,
    OrderDetail,
    OrderLineList,
    OrderLineDetail,
    OrderLineAttributeDetail,
    UserAddressList,
    UserAddressDetail,
) = get_api_classes(
    "views.checkout",
    [
        "CheckoutView",
        "OrderList",
        "OrderDetail",
        "OrderLineList",
        "OrderLineDetail",
        "OrderLineAttributeDetail",
        "UserAddressList",
        "UserAddressDetail",
    ],
)

(
    ServiceAdminList,
    ServiceAdminDetail,
    ServiceClassAdminList,
    ServiceClassAdminDetail,
    ServiceAttributeAdminList,
    ServiceAttributeAdminDetail,
    AttributeOptionGroupAdminList,
    AttributeOptionGroupAdminDetail,
    CategoryAdminList,
    CategoryAdminDetail,
) = get_api_classes(
    "views.admin.service",
    [
        "ServiceAdminList",
        "ServiceAdminDetail",
        "ServiceClassAdminList",
        "ServiceClassAdminDetail",
        "ServiceAttributeAdminList",
        "ServiceAttributeAdminDetail",
        "AttributeOptionGroupAdminList",
        "AttributeOptionGroupAdminDetail",
        "CategoryAdminList",
        "CategoryAdminDetail",
    ],
)

(
    OrderAdminList,
    OrderAdminDetail,
    OrderLineAdminList,
    OrderLineAdminDetail,
    OrderLineAttributeAdminDetail,
) = get_api_classes(
    "views.admin.order",
    [
        "OrderAdminList",
        "OrderAdminDetail",
        "OrderLineAdminList",
        "OrderLineAdminDetail",
        "OrderLineAttributeAdminDetail",
    ],
)

(UserAdminList, UserAdminDetail) = get_api_classes(
    "views.admin.user", ["UserAdminList", "UserAdminDetail"]
)

urlpatterns = [
    path("", api_root, name="api-root"),
    path("register/", RegistrationView.as_view(), name="api-register"),
    path("login/", LoginView.as_view(), name="api-login"),
    path("basket/", BasketView.as_view(), name="api-basket"),
    path(
        "basket/add-service/", AddServiceView.as_view(), name="api-basket-add-service"
    ),
    path(
        "basket/add-voucher/", AddVoucherView.as_view(), name="api-basket-add-voucher"
    ),
    path(
        "basket/shipping-methods/",
        ShippingMethodView.as_view(),
        name="api-basket-shipping-methods",
    ),
    path("baskets/", BasketList.as_view(), name="basket-list"),
    path("baskets/<int:pk>/", BasketDetail.as_view(), name="basket-detail"),
    path("baskets/<int:pk>/lines/", LineList.as_view(), name="basket-lines-list"),
    path(
        "baskets/<int:basket_pk>/lines/<int:pk>/",
        BasketLineDetail.as_view(),
        name="basket-line-detail",
    ),
    path(
        "baskets/<int:basket_pk>/lines/<int:line_pk>/lineattributes/<int:pk>/",
        LineAttributeDetail.as_view(),
        name="lineattribute-detail",
    ),
    path("services/", ServiceList.as_view(), name="service-list"),
    path("services/<int:pk>/", ServiceDetail.as_view(), name="service-detail"),
    path("services/<int:pk>/price/", ServicePrice.as_view(), name="service-price"),
    path(
        "services/<int:pk>/availability/",
        ServiceAvailability.as_view(),
        name="service-availability",
    ),
    path(
        "services/<int:pk>/stockrecords/",
        ServiceStockRecords.as_view(),
        name="service-stockrecords",
    ),
    path(
        "services/<int:service_pk>/stockrecords/<int:pk>/",
        ServiceStockRecordDetail.as_view(),
        name="service-stockrecord-detail",
    ),
    path("options/", OptionList.as_view(), name="option-list"),
    path("options/<int:pk>/", OptionDetail.as_view(), name="option-detail"),
    path("ranges/", RangeList.as_view(), name="range-list"),
    path("ranges/<int:pk>/", RangeDetail.as_view(), name="range-detail"),
    path("categories/", CategoryList.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryDetail.as_view(), name="category-detail"),
    re_path(
        "^categories/(?P<breadcrumbs>.*)/$",
        CategoryList.as_view(),
        name="category-child-list",
    ),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("checkout/", CheckoutView.as_view(), name="api-checkout"),
    path("orders/", OrderList.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetail.as_view(), name="order-detail"),
    path("orders/<int:pk>/lines/", OrderLineList.as_view(), name="order-lines-list"),
    path("orderlines/<int:pk>/", OrderLineDetail.as_view(), name="order-lines-detail"),
    path(
        "orderlineattributes/<int:pk>/",
        OrderLineAttributeDetail.as_view(),
        name="order-lineattributes-detail",
    ),
    path("countries/", CountryList.as_view(), name="country-list"),
    re_path(
        r"^countries/(?P<pk>[A-z]{2})/$", CountryDetail.as_view(), name="country-detail"
    ),
    path("useraddresses/", UserAddressList.as_view(), name="useraddress-list"),
    path(
        "useraddresses/<int:pk>/",
        UserAddressDetail.as_view(),
        name="useraddress-detail",
    ),
]

admin_urlpatterns = [
    path("services/", ServiceAdminList.as_view(), name="admin-service-list"),
    path(
        "services/<int:pk>/",
        ServiceAdminDetail.as_view(),
        name="admin-service-detail",
    ),
    path(
        "serviceclasses/",
        ServiceClassAdminList.as_view(),
        name="admin-serviceclass-list",
    ),
    path(
        "serviceclasses/<slug:slug>/",
        ServiceClassAdminDetail.as_view(),
        name="admin-serviceclass-detail",
    ),
    path("categories/", CategoryAdminList.as_view(), name="admin-category-list"),
    path(
        "categories/<int:pk>/",
        CategoryAdminDetail.as_view(),
        name="admin-category-detail",
    ),
    re_path(
        r"^categories/(?P<breadcrumbs>.*)/$",
        CategoryAdminList.as_view(),
        name="admin-category-child-list",
    ),
    path(
        "serviceattributes/",
        ServiceAttributeAdminList.as_view(),
        name="admin-serviceattribute-list",
    ),
    path(
        "stockrecords/<int:pk>/",
        StockRecordDetail.as_view(),
        name="admin-stockrecord-detail",
    ),
    path("partners/", PartnerList.as_view(), name="admin-partner-list"),
    path("partners/<int:pk>/", PartnerDetail.as_view(), name="partner-detail"),
    path(
        "serviceattributes/<int:pk>/",
        ServiceAttributeAdminDetail.as_view(),
        name="admin-serviceattribute-detail",
    ),
    path(
        "attributeoptiongroups/",
        AttributeOptionGroupAdminList.as_view(),
        name="admin-attributeoptiongroup-list",
    ),
    path(
        "attributeoptiongroups/<int:pk>/",
        AttributeOptionGroupAdminDetail.as_view(),
        name="admin-attributeoptiongroup-detail",
    ),
    path("orders/", OrderAdminList.as_view(), name="admin-order-list"),
    path("orders/<int:pk>/", OrderAdminDetail.as_view(), name="admin-order-detail"),
    path(
        "orders/<int:pk>/lines/",
        OrderLineAdminList.as_view(),
        name="admin-order-lines-list",
    ),
    path(
        "orderlines/<int:pk>/",
        OrderLineAdminDetail.as_view(),
        name="admin-order-lines-detail",
    ),
    path(
        "orderlineattributes/<int:pk>/",
        OrderLineAttributeAdminDetail.as_view(),
        name="admin-order-lineattributes-detail",
    ),
    path("users/", UserAdminList.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", UserAdminDetail.as_view(), name="admin-user-detail"),
]

if not getattr(settings, "OSCARAPI_BLOCK_ADMIN_API_ACCESS", True):
    urlpatterns.append(path("admin/", include(admin_urlpatterns)))

urlpatterns = format_suffix_patterns(urlpatterns)
