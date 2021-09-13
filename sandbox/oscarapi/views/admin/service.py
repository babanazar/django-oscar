# pylint: disable=unbalanced-tuple-unpacking
from django.http import Http404
from rest_framework import generics
from rest_framework.exceptions import NotFound

from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.utils.exists import construct_id_filter

APIAdminPermission = get_api_class("permissions", "APIAdminPermission")
ServiceAttributeSerializer, AttributeOptionGroupSerializer = get_api_classes(
    "serializers.service",
    ["ServiceAttributeSerializer", "AttributeOptionGroupSerializer"],
)
(
    AdminServiceSerializer,
    AdminCategorySerializer,
    AdminServiceClassSerializer,
) = get_api_classes(
    "serializers.admin.service",
    [
        "AdminServiceSerializer",
        "AdminCategorySerializer",
        "AdminServiceClassSerializer",
    ],
)
CategoryList = get_api_class("views.service", "CategoryList")
Service = get_model("catalogue", "Service")
Category = get_model("catalogue", "Category")
ServiceAttribute = get_model("catalogue", "ServiceAttribute")
ServiceClass = get_model("catalogue", "ServiceClass")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")


class ServiceAdminList(generics.UpdateAPIView, generics.ListCreateAPIView):
    """
    Use this api for synchronizing data from another datasource.

    This api endpoint supports POST, PUT and PATCH, which means it can be used
    for creating, but also for updating. There is no need to supply the
    primary key(id) of the service, as long as you are sending enough data
    to uniquely identify the service (upc). That means you can try updating and
    if that fails, try POST. Or the other way around, whatever makes most
    sense in you scenario.

    Note that if you have changed the service model and changed upc to no longer
    be unique, you MUST add another unique field or specify a unique together
    constraint. And you have to send that data along.
    """

    serializer_class = AdminServiceSerializer
    queryset = Service.objects.get_queryset()
    permission_classes = (APIAdminPermission,)

    def get_object(self):
        """
        Returns the object the view is displaying.

        Tries to extract a uniquely identifying query from the posted data
        """
        try:
            automatic_filter = construct_id_filter(Service, self.request.data)
            if automatic_filter:
                obj = Service.objects.get(automatic_filter)
                self.check_object_permissions(self.request, obj)
                return obj
            else:
                raise NotFound(
                    "Not enough info to identify %s." % Service._meta.object_name
                )
        except Service.DoesNotExist:
            raise Http404("No %s matches the given query." % Service._meta.object_name)


class ServiceAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminServiceSerializer
    queryset = Service.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ServiceClassAdminList(generics.ListCreateAPIView):
    serializer_class = AdminServiceClassSerializer
    queryset = ServiceClass.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ServiceClassAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminServiceClassSerializer
    queryset = ServiceClass.objects.get_queryset()
    permission_classes = (APIAdminPermission,)
    lookup_field = "slug"


class ServiceAttributeAdminList(generics.ListCreateAPIView):
    serializer_class = ServiceAttributeSerializer
    queryset = ServiceAttribute.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class ServiceAttributeAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceAttributeSerializer
    queryset = ServiceAttribute.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class AttributeOptionGroupAdminList(generics.ListCreateAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class AttributeOptionGroupAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttributeOptionGroupSerializer
    queryset = AttributeOptionGroup.objects.get_queryset()
    permission_classes = (APIAdminPermission,)


class CategoryAdminList(generics.ListCreateAPIView, CategoryList):
    queryset = Category.get_root_nodes()
    serializer_class = AdminCategorySerializer
    permission_classes = (APIAdminPermission,)

    def get_queryset(self):
        try:
            return super(CategoryAdminList, self).get_queryset()
        except NotFound:  # admins might be able to create so hold the error.
            return Category.objects.none()

    def get_serializer_context(self):
        ctx = super(CategoryAdminList, self).get_serializer_context()
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)

        if breadcrumb_path is not None:
            ctx["breadcrumbs"] = breadcrumb_path

        return ctx


class CategoryAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = AdminCategorySerializer
    permission_classes = (APIAdminPermission,)
