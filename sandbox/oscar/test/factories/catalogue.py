# coding=utf-8
import factory

from oscar.core.loading import get_model

__all__ = [
    'ServiceClassFactory', 'ServiceFactory',
    'CategoryFactory', 'ServiceCategoryFactory',
    'ServiceAttributeFactory', 'AttributeOptionGroupFactory',
    'OptionFactory', 'AttributeOptionFactory',
    'ServiceAttributeValueFactory', 'ServiceReviewFactory',
    'ServiceImageFactory'
]


class ServiceClassFactory(factory.django.DjangoModelFactory):
    name = "Books"
    requires_shipping = True
    track_stock = True

    class Meta:
        model = get_model('catalogue', 'ServiceClass')


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Service')

    structure = Meta.model.STANDALONE
    upc = factory.Sequence(lambda n: '978080213020%d' % n)
    title = "A confederacy of dunces"
    service_class = factory.SubFactory(ServiceClassFactory)

    stockrecords = factory.RelatedFactory(
        'oscar.test.factories.StockRecordFactory', 'service')
    categories = factory.RelatedFactory(
        'oscar.test.factories.ServiceCategoryFactory', 'service')


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Category %d' % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 1
    path = factory.Sequence(lambda n: '%04d' % n)

    class Meta:
        model = get_model('catalogue', 'Category')


class ServiceCategoryFactory(factory.django.DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = get_model('catalogue', 'ServiceCategory')


class ServiceAttributeFactory(factory.django.DjangoModelFactory):
    code = name = 'weight'
    service_class = factory.SubFactory(ServiceClassFactory)
    type = "float"

    class Meta:
        model = get_model('catalogue', 'ServiceAttribute')


class OptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Option')

    name = 'example option'
    code = 'example'
    type = Meta.model.TEXT
    required = False


class AttributeOptionFactory(factory.django.DjangoModelFactory):
    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: 'Option %d' % n)

    class Meta:
        model = get_model('catalogue', 'AttributeOption')


class AttributeOptionGroupFactory(factory.django.DjangoModelFactory):
    name = 'Grüppchen'

    class Meta:
        model = get_model('catalogue', 'AttributeOptionGroup')


class ServiceAttributeValueFactory(factory.django.DjangoModelFactory):
    attribute = factory.SubFactory(ServiceAttributeFactory)
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = get_model('catalogue', 'ServiceAttributeValue')


class ServiceReviewFactory(factory.django.DjangoModelFactory):
    score = 5
    service = factory.SubFactory(ServiceFactory, stockrecords=[])

    class Meta:
        model = get_model('reviews', 'ServiceReview')


class ServiceImageFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory, stockrecords=[])
    original = factory.django.ImageField(width=100, height=200, filename='test_image.jpg')

    class Meta:
        model = get_model('catalogue', 'ServiceImage')
