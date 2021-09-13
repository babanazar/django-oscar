# pylint: disable=unbalanced-tuple-unpacking
from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model

from oscarapi.utils.categories import find_from_full_slug
from oscarapi.utils.loading import get_api_classes, get_api_class

Selector = get_class("partner.strategy", "Selector")
(
    CategorySerializer,
    ServiceLinkSerializer,
    ServiceSerializer,
    ServiceStockRecordSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.service",
    [
        "CategorySerializer",
        "ServiceLinkSerializer",
        "ServiceSerializer",
        "ServiceStockRecordSerializer",
        "AvailabilitySerializer",
    ],
)

PriceSerializer = get_api_class("serializers.checkout", "PriceSerializer")


__all__ = ("ServiceList", "ServiceDetail", "ServicePrice", "ServiceAvailability")

Service = get_model("catalogue", "Service")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")


class ServiceList(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceLinkSerializer

    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent services can
        be selected separately, eg::

            http://127.0.0.1:8000/api/services/?structure=standalone

        or::

            http://127.0.0.1:8000/api/services/?structure=parent
        """
        qs = super(ServiceList, self).get_queryset()
        structure = self.request.query_params.get("structure")
        if structure is not None:
            return qs.filter(structure=structure)

        return qs


class ServiceDetail(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class ServicePrice(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = PriceSerializer

    def get(
        self, request, pk=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        service = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_service(service).price, context={"request": request}
        )
        return Response(ser.data)


class ServiceStockRecords(generics.ListAPIView):
    serializer_class = ServiceStockRecordSerializer
    queryset = StockRecord.objects.all()

    def get_queryset(self):
        service_pk = self.kwargs.get("pk")
        return super().get_queryset().filter(service_id=service_pk)


class ServiceStockRecordDetail(generics.RetrieveAPIView):
    serializer_class = ServiceStockRecordSerializer
    queryset = StockRecord.objects.all()


class ServiceAvailability(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = AvailabilitySerializer

    def get(
        self, request, pk=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        service = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_service(service).availability,
            context={"request": request},
        )
        return Response(ser.data)


class CategoryList(generics.ListAPIView):
    queryset = Category.get_root_nodes()
    serializer_class = CategorySerializer

    def get_queryset(self):
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)
        if breadcrumb_path is None:
            return super(CategoryList, self).get_queryset()

        return find_from_full_slug(breadcrumb_path, separator="/").get_children()


class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
