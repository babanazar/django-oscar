import logging
from copy import deepcopy
from django.utils.translation import ugettext as _

from rest_framework import serializers
from rest_framework.fields import empty

from oscar.core.loading import get_model

from oscarapi.utils.exists import bound_unique_together_get_or_create_multiple
from oscarapi.utils.loading import get_api_classes
from oscarapi.utils.settings import overridable
from oscarapi.utils.files import file_hash
from oscarapi.utils.exists import find_existing_attribute_option_group
from oscarapi.utils.accessors import getitems

from oscarapi.serializers.fields import DrillDownHyperlinkedIdentityField
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
    UpdateListSerializer,
    UpdateForwardManyToManySerializer,
)

from .exceptions import FieldError

logger = logging.getLogger(__name__)
Service = get_model("catalogue", "Service")
Range = get_model("offer", "Range")
ServiceAttributeValue = get_model("catalogue", "ServiceAttributeValue")
ServiceImage = get_model("catalogue", "ServiceImage")
Option = get_model("catalogue", "Option")
Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")
ServiceClass = get_model("catalogue", "ServiceClass")
ServiceAttribute = get_model("catalogue", "ServiceAttribute")
Category = get_model("catalogue", "Category")
AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeValueField, CategoryField, SingleValueSlugRelatedField = get_api_classes(
    "serializers.fields",
    ["AttributeValueField", "CategoryField", "SingleValueSlugRelatedField"],
)


class AttributeOptionGroupSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-attributeoptiongroup-detail"
    )
    options = SingleValueSlugRelatedField(
        many=True,
        required=True,
        slug_field="option",
        queryset=AttributeOption.objects.get_queryset(),
    )

    def create(self, validated_data):
        existing_option = find_existing_attribute_option_group(
            validated_data["name"], validated_data["options"]
        )
        if existing_option is not None:
            return existing_option
        else:
            options = validated_data.pop("options", None)
            instance = super(AttributeOptionGroupSerializer, self).create(
                validated_data
            )
            options = bound_unique_together_get_or_create_multiple(
                instance.options, options
            )
            instance.options.set(options)
            return instance

    def update(self, instance, validated_data):
        existing_option = find_existing_attribute_option_group(
            validated_data["name"], validated_data["options"]
        )
        if existing_option is not None:
            return existing_option
        else:
            options = validated_data.pop("options", None)
            updated_instance = super(AttributeOptionGroupSerializer, self).update(
                instance, validated_data
            )
            # if the field was returned unbound,
            options = bound_unique_together_get_or_create_multiple(
                updated_instance.options, options
            )
            updated_instance.options.set(options, bulk=False)
            if not self.partial:
                # we need to manually remove the options
                updated_instance.options.exclude(
                    pk__in=[o.pk for o in options]
                ).delete()

            return updated_instance

    class Meta:
        model = AttributeOptionGroup
        fields = "__all__"


class BaseCategorySerializer(OscarHyperlinkedModelSerializer):
    breadcrumbs = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = Category
        exclude = ("path", "depth", "numchild")


class CategorySerializer(BaseCategorySerializer):
    children = serializers.HyperlinkedIdentityField(
        view_name="category-child-list",
        lookup_field="full_slug",
        lookup_url_kwarg="breadcrumbs",
    )


class ServiceAttributeListSerializer(UpdateListSerializer):
    def select_existing_item(self, manager, datum):
        try:
            return manager.get(service_class=datum["service_class"], code=datum["code"])
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned as e:
            logger.error("Multiple objects on unique contrained items, freaky %s", e)
            logger.exception(e)

        return None


class ServiceAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="admin-serviceattribute-detail"
    )
    service_class = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=ServiceClass.objects.get_queryset(),
        write_only=True,
        required=False,
    )
    option_group = AttributeOptionGroupSerializer(required=False, allow_null=True)

    def create(self, validated_data):
        option_group = validated_data.pop("option_group", None)
        instance = super(ServiceAttributeSerializer, self).create(validated_data)
        return self.update(instance, {"option_group": option_group})

    def update(self, instance, validated_data):
        option_group = validated_data.pop("option_group", None)
        updated_instance = super(ServiceAttributeSerializer, self).update(
            instance, validated_data
        )
        if option_group is not None:
            serializer = self.fields["option_group"]
            # use the serializer to update the attribute_values
            if instance.option_group:
                updated_instance.option_group = serializer.update(
                    instance.option_group, option_group
                )
            else:
                updated_instance.option_group = serializer.create(option_group)

            updated_instance.save()

        return updated_instance

    class Meta:
        model = ServiceAttribute
        list_serializer_class = ServiceAttributeListSerializer
        fields = "__all__"


class RangeSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Range
        fields = "__all__"


class PartnerSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Partner
        fields = "__all__"


class OptionSerializer(OscarHyperlinkedModelSerializer):
    code = serializers.SlugField()

    class Meta:
        model = Option
        fields = overridable("OSCARAPI_OPTION_FIELDS", default="__all__")
        list_serializer_class = UpdateForwardManyToManySerializer


class ServiceAttributeValueListSerializer(UpdateListSerializer):
    def get_value(self, dictionary):
        values = super(ServiceAttributeValueListSerializer, self).get_value(dictionary)
        if values is empty:
            return values

        service_class, parent = getitems(dictionary, "service_class", "parent")
        return [
            dict(value, service_class=service_class, parent=parent) for value in values
        ]


class ServiceAttributeValueSerializer(OscarModelSerializer):
    # we declare the service as write_only since this serializer is meant to be
    # used nested inside a service serializer.
    service = serializers.PrimaryKeyRelatedField(
        many=False, write_only=True, required=False, queryset=Service.objects
    )

    value = AttributeValueField()  # handles different attribute value types
    # while code is specified as read_only, it is still required, because otherwise
    # the attribute is unknown, so while it will never be overwritten, you do
    # have to include it in your data structure
    code = serializers.CharField(source="attribute.code", read_only=True)
    name = serializers.CharField(
        source="attribute.name", required=False, read_only=True
    )

    def to_internal_value(self, data):
        try:
            internal_value = super(
                ServiceAttributeValueSerializer, self
            ).to_internal_value(data)
            internal_value["service_class"] = data.get("service_class")
            return internal_value
        except FieldError as e:
            raise serializers.ValidationError(e.detail)

    def save(self, **kwargs):
        """
        Since there is a unique constraint, sometimes we want to update instead
        of creating a new object (because an integrity error would occur due
        to the constraint on attribute and service). If instance is set, the
        update method will be used instead of the create method.
        """
        data = deepcopy(kwargs)
        data.update(self.validated_data)
        return self.update_or_create(data)

    def update_or_create(self, validated_data):
        value = validated_data["value"]
        service = validated_data["service"]
        attribute = validated_data["attribute"]
        attribute.save_value(service, value)
        return service.attribute_values.get(attribute=attribute)

    create = update_or_create

    def update(self, instance, validated_data):
        data = deepcopy(validated_data)
        data["service"] = instance.service
        return self.update_or_create(data)

    class Meta:
        model = ServiceAttributeValue
        list_serializer_class = ServiceAttributeValueListSerializer
        fields = overridable(
            "OSCARAPI_PRODUCT_ATTRIBUTE_VALUE_FIELDS",
            default=("name", "value", "code", "service"),
        )


class ServiceImageUpdateListSerializer(UpdateListSerializer):
    "Select existing image based on hash of image content"

    def select_existing_item(self, manager, datum):
        # determine the hash of the passed image
        target_file_hash = file_hash(datum["original"])
        for image in manager.all():  # search for a match in the set of exising images
            _hash = file_hash(image.original)
            if _hash == target_file_hash:
                # django will create a copy of the original under a weird name,
                # because the image is freshly fetched, except if we use the
                # original image FileObject
                datum["original"] = image.original
                return image

        return None


class ServiceImageSerializer(OscarModelSerializer):
    service = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, queryset=Service.objects
    )

    class Meta:
        model = ServiceImage
        fields = "__all__"
        list_serializer_class = ServiceImageUpdateListSerializer


class AvailabilitySerializer(serializers.Serializer):  # pylint: disable=abstract-method
    is_available_to_buy = serializers.BooleanField()
    num_available = serializers.IntegerField(required=False)
    message = serializers.CharField()


class RecommmendedServiceSerializer(OscarModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="service-detail")

    class Meta:
        model = Service
        fields = overridable("OSCARAPI_RECOMMENDED_PRODUCT_FIELDS", default=("url",))


class ServiceStockRecordSerializer(OscarModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name="service-stockrecord-detail",
        extra_url_kwargs={"service_pk": "service_id"},
    )

    class Meta:
        model = StockRecord
        fields = "__all__"


class BaseServiceSerializer(OscarModelSerializer):
    "Base class shared by admin and public serializer"
    attributes = ServiceAttributeValueSerializer(
        many=True, required=False, source="attribute_values"
    )
    categories = CategoryField(many=True, required=False)
    service_class = serializers.SlugRelatedField(
        slug_field="slug", queryset=ServiceClass.objects, allow_null=True
    )
    options = OptionSerializer(many=True, required=False)
    recommended_services = serializers.HyperlinkedRelatedField(
        view_name="service-detail",
        many=True,
        required=False,
        queryset=Service.objects.filter(
            structure__in=[Service.PARENT, Service.STANDALONE]
        ),
    )

    def validate(self, attrs):
        if "structure" in attrs and "parent" in attrs:
            if attrs["structure"] == Service.CHILD and attrs["parent"] is None:
                raise serializers.ValidationError(_("child without parent"))
        if "structure" in attrs and "service_class" in attrs:
            if attrs["service_class"] is None and attrs["structure"] != Service.CHILD:
                raise serializers.ValidationError(
                    _("service_class can not be empty for structure %(structure)s")
                    % attrs
                )

        return super(BaseServiceSerializer, self).validate(attrs)

    class Meta:
        model = Service


class PublicServiceSerializer(BaseServiceSerializer):
    "Serializer base class used for public services api"
    url = serializers.HyperlinkedIdentityField(view_name="service-detail")
    price = serializers.HyperlinkedIdentityField(
        view_name="service-price", read_only=True
    )
    availability = serializers.HyperlinkedIdentityField(
        view_name="service-availability", read_only=True
    )

    def get_field_names(self, declared_fields, info):
        """
        Override get_field_names to make sure that we are not getting errors
        for not including declared fields.
        """
        return super(PublicServiceSerializer, self).get_field_names({}, info)


class ChildServiceserializer(PublicServiceSerializer):
    "Serializer for child services"
    parent = serializers.HyperlinkedRelatedField(
        view_name="service-detail",
        queryset=Service.objects.filter(structure=Service.PARENT),
    )
    # the below fields can be filled from the parent service if enabled.
    images = ServiceImageSerializer(many=True, required=False, source="parent.images")
    description = serializers.CharField(source="parent.description")

    class Meta(PublicServiceSerializer.Meta):
        fields = overridable(
            "OSCARAPI_CHILDPRODUCTDETAIL_FIELDS",
            default=(
                "url",
                "upc",
                "id",
                "title",
                "structure",
                # 'parent', 'description', 'images', are not included by default, but
                # easily enabled by overriding OSCARAPI_CHILDPRODUCTDETAIL_FIELDS
                # in your settings file
                "date_created",
                "date_updated",
                "recommended_services",
                "attributes",
                "categories",
                "service_class",
                "price",
                "availability",
                "options",
            ),
        )


class ServiceSerializer(PublicServiceSerializer):
    "Serializer for public api with strategy fields added for price and availability"
    url = serializers.HyperlinkedIdentityField(view_name="service-detail")
    price = serializers.HyperlinkedIdentityField(
        view_name="service-price", read_only=True
    )
    availability = serializers.HyperlinkedIdentityField(
        view_name="service-availability", read_only=True
    )

    images = ServiceImageSerializer(many=True, required=False)
    children = ChildServiceserializer(many=True, required=False)

    stockrecords = serializers.HyperlinkedIdentityField(
        view_name="service-stockrecords", read_only=True
    )

    class Meta(PublicServiceSerializer.Meta):
        fields = overridable(
            "OSCARAPI_PRODUCTDETAIL_FIELDS",
            default=(
                "url",
                "upc",
                "id",
                "title",
                "description",
                "structure",
                "date_created",
                "date_updated",
                "recommended_services",
                "attributes",
                "categories",
                "service_class",
                "images",
                "price",
                "availability",
                "stockrecords",
                "options",
                "children",
            ),
        )


class ServiceLinkSerializer(ServiceSerializer):
    """
    Summary serializer for list view, listing all services.

    This serializer can be easily made to show any field on ``ServiceSerializer``,
    just add fields to the ``OSCARAPI_PRODUCT_FIELDS`` setting.
    """

    class Meta(PublicServiceSerializer.Meta):
        fields = overridable(
            "OSCARAPI_PRODUCT_FIELDS", default=("url", "id", "upc", "title")
        )


class OptionValueSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    option = serializers.HyperlinkedRelatedField(
        view_name="option-detail", queryset=Option.objects
    )
    value = serializers.CharField()


class AddServiceSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializes and validates an add to basket request.
    """

    quantity = serializers.IntegerField(required=True)
    url = serializers.HyperlinkedRelatedField(
        view_name="service-detail", queryset=Service.objects, required=True
    )
    options = OptionValueSerializer(many=True, required=False)
