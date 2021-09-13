from rest_framework import serializers

from oscar.core.loading import get_model
from oscarapi.serializers.utils import (
    DelayUniqueSerializerMixin,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer,
)

Service = get_model("catalogue", "Service")
StockRecord = get_model("partner", "StockRecord")


class AdminStockRecordSerializer(
    DelayUniqueSerializerMixin, OscarHyperlinkedModelSerializer
):
    url = serializers.HyperlinkedIdentityField(view_name="admin-stockrecord-detail")

    service = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=Service.objects
    )

    class Meta:
        model = StockRecord
        fields = "__all__"
        list_serializer_class = UpdateListSerializer
