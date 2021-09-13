from django.test import TestCase

from oscar.apps.catalogue import models as catalogue_models
from oscar.apps.offer import models
from oscar.test.factories import create_service


class TestWholeSiteRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All services", includes_all_services=True)
        self.prod = create_service()

    def test_all_services_range(self):
        self.assertTrue(self.range.contains_service(self.prod))
        self.assertIn(self.range, models.Range.objects.contains_service(self.prod))

    def test_all_services_includes_child_services(self):
        child_service = create_service(structure='child', parent=self.prod)
        self.assertTrue(child_service in self.range.all_services())

    def test_whitelisting(self):
        self.range.add_service(self.prod)
        self.assertTrue(self.range.contains_service(self.prod))
        self.assertIn(self.prod, self.range.all_services())

    def test_blacklisting(self):
        self.range.excluded_services.add(self.prod)
        self.assertFalse(self.range.contains_service(self.prod))
        self.assertNotIn(self.prod, self.range.all_services())


class TestChildRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name='Child-specific range', includes_all_services=False)
        self.parent = create_service(structure='parent')
        self.child1 = create_service(structure='child', parent=self.parent)
        self.child2 = create_service(structure='child', parent=self.parent)
        self.range.add_service(self.child1)

    def test_includes_child(self):
        self.assertTrue(self.range.contains_service(self.child1))

    def test_does_not_include_parent(self):
        self.assertFalse(self.range.contains_service(self.parent))

    def test_does_not_include_sibling(self):
        self.assertFalse(self.range.contains_service(self.child2))

    def test_parent_with_child_exception(self):
        self.range.add_service(self.parent)
        self.range.remove_service(self.child1)
        self.assertTrue(self.range.contains_service(self.parent))
        self.assertTrue(self.range.contains_service(self.child2))
        self.assertFalse(self.range.contains_service(self.child1))


class TestParentRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name='Parent-specific range', includes_all_services=False)
        self.parent = create_service(structure='parent')
        self.child1 = create_service(structure='child', parent=self.parent)
        self.child2 = create_service(structure='child', parent=self.parent)

    def test_includes_all_children_when_parent_in_included_services(self):
        self.range.add_service(self.parent)
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertTrue(self.range.contains_service(self.child2))

    def test_includes_all_children_when_parent_in_categories(self):
        included_category = catalogue_models.Category.add_root(name="root")
        self.range.included_categories.add(included_category)
        self.parent.categories.add(included_category)
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertTrue(self.range.contains_service(self.child2))


class TestPartialRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All services", includes_all_services=False)
        self.parent = create_service(structure='parent')
        self.child = create_service(structure='child', parent=self.parent)

    def test_empty_list(self):
        self.assertFalse(self.range.contains_service(self.parent))
        self.assertFalse(self.range.contains_service(self.child))

    def test_included_classes(self):
        self.range.classes.add(self.parent.get_service_class())
        self.assertTrue(self.range.contains_service(self.parent))
        self.assertTrue(self.range.contains_service(self.child))

    def test_includes(self):
        self.range.add_service(self.parent)
        self.assertTrue(self.range.contains_service(self.parent))
        self.assertTrue(self.range.contains_service(self.child))

    def test_included_class_with_exception(self):
        self.range.classes.add(self.parent.get_service_class())
        self.range.excluded_services.add(self.parent)
        self.assertFalse(self.range.contains_service(self.parent))
        self.assertFalse(self.range.contains_service(self.child))

    def test_included_excluded_services_in_all_services(self):
        count = 5
        included_services = [create_service() for _ in range(count)]
        excluded_services = [create_service() for _ in range(count)]

        for service in included_services:
            models.RangeService.objects.create(
                service=service, range=self.range)

        self.range.excluded_services.add(*excluded_services)

        all_services = self.range.all_services()
        self.assertEqual(all_services.count(), count)
        self.assertEqual(self.range.num_services(), count)

        for service in included_services:
            self.assertTrue(service in all_services)

        for service in excluded_services:
            self.assertTrue(service not in all_services)

    def test_service_classes_in_all_services(self):
        service_in_included_class = create_service(service_class="123")
        included_service_class = service_in_included_class.service_class
        excluded_service_in_included_class = create_service(
            service_class=included_service_class.name)

        self.range.classes.add(included_service_class)
        self.range.excluded_services.add(excluded_service_in_included_class)

        all_services = self.range.all_services()
        self.assertTrue(service_in_included_class in all_services)
        self.assertTrue(excluded_service_in_included_class not in
                        all_services)

        self.assertEqual(self.range.num_services(), 1)

    def test_categories_in_all_services(self):
        included_category = catalogue_models.Category.add_root(name="root")
        service_in_included_category = create_service()
        excluded_service_in_included_category = create_service()

        catalogue_models.ServiceCategory.objects.create(
            service=service_in_included_category, category=included_category)
        catalogue_models.ServiceCategory.objects.create(
            service=excluded_service_in_included_category,
            category=included_category)

        self.range.included_categories.add(included_category)
        self.range.excluded_services.add(excluded_service_in_included_category)

        all_services = self.range.all_services()
        self.assertTrue(service_in_included_category in all_services)
        self.assertTrue(excluded_service_in_included_category not in
                        all_services)

        self.assertEqual(self.range.num_services(), 1)

    def test_descendant_categories_in_all_services(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")

        c_service = create_service()
        gc_service = create_service()

        catalogue_models.ServiceCategory.objects.create(
            service=c_service, category=child_category)
        catalogue_models.ServiceCategory.objects.create(
            service=gc_service, category=grand_child_category)

        self.range.included_categories.add(parent_category)

        all_services = self.range.all_services()
        self.assertTrue(c_service in all_services)
        self.assertTrue(gc_service in all_services)

        self.assertEqual(self.range.num_services(), 2)

    def test_service_duplicated_in_all_services(self):
        """Making sure service is not duplicated in range services if it has multiple categories assigned."""

        included_category1 = catalogue_models.Category.add_root(name="cat1")
        included_category2 = catalogue_models.Category.add_root(name="cat2")
        service = create_service()
        catalogue_models.ServiceCategory.objects.create(
            service=service, category=included_category1)
        catalogue_models.ServiceCategory.objects.create(
            service=service, category=included_category2)

        self.range.included_categories.add(included_category1)
        self.range.included_categories.add(included_category2)
        self.range.add_service(service)

        all_service_ids = list(self.range.all_services().values_list('id', flat=True))
        service_occurances_in_range = all_service_ids.count(service.id)
        self.assertEqual(service_occurances_in_range, 1)

    def test_service_remove_from_range(self):
        included_category = catalogue_models.Category.add_root(name="root")
        service = create_service()
        catalogue_models.ServiceCategory.objects.create(
            service=service, category=included_category)

        self.range.included_categories.add(included_category)
        self.range.add_service(service)

        all_services = self.range.all_services()
        self.assertTrue(service in all_services)

        self.range.remove_service(service)

        all_services = self.range.all_services()
        self.assertFalse(service in all_services)

        # Re-adding service should return it to the services range
        self.range.add_service(service)

        all_services = self.range.all_services()
        self.assertTrue(service in all_services)

    def test_range_is_reordable(self):
        service = create_service()
        self.range.add_service(service)
        self.assertTrue(self.range.is_reorderable)

        included_category = catalogue_models.Category.add_root(name="root")
        catalogue_models.ServiceCategory.objects.create(
            service=service, category=included_category)
        self.range.included_categories.add(included_category)

        self.range.invalidate_cached_queryset()
        self.assertFalse(self.range.is_reorderable)

        self.range.included_categories.remove(included_category)
        self.range.invalidate_cached_queryset()
        self.assertTrue(self.range.is_reorderable)


class TestRangeModel(TestCase):

    def test_ensures_unique_slugs_are_used(self):
        first_range = models.Range.objects.create(name="Foo")
        first_range.name = "Bar"
        first_range.save()
        models.Range.objects.create(name="Foo")


class TestRangeQuerySet(TestCase):
    def setUp(self):
        self.prod = create_service()
        self.excludedprod = create_service()
        self.parent = create_service(structure="parent")
        self.child1 = create_service(structure="child", parent=self.parent)
        self.child2 = create_service(structure="child", parent=self.parent)

        self.range = models.Range.objects.create(
            name="All services", includes_all_services=True
        )
        self.range.excluded_services.add(self.excludedprod)
        self.range.excluded_services.add(self.child2)

        self.childrange = models.Range.objects.create(
            name="Child-specific range", includes_all_services=False
        )
        self.childrange.add_service(self.child1)
        self.childrange.add_service(self.prod)

    def test_contains_service(self):
        ranges = models.Range.objects.contains_service(self.prod)
        self.assertEqual(ranges.count(), 2, "Both ranges should contain the service")

    def test_excluded_service(self):
        ranges = models.Range.objects.contains_service(self.excludedprod)
        self.assertEqual(
            ranges.count(), 0, "No ranges should contain the excluded service"
        )

    def test_contains_child(self):
        ranges = models.Range.objects.contains_service(self.child1)
        self.assertEqual(
            ranges.count(), 2, "Both ranges should contain the child service"
        )

    def test_contains_parent(self):
        ranges = models.Range.objects.contains_service(self.parent)
        self.assertEqual(
            ranges.count(), 1, "Both ranges should contain the parent service"
        )

    def test_exclude_child(self):
        ranges = models.Range.objects.contains_service(self.child2)
        self.assertEqual(
            ranges.count(), 1, "Only 1 range should contain the second child"
        )

    def test_category(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")
        catalogue_models.ServiceCategory.objects.create(
            service=self.parent, category=grand_child_category
        )

        cat_range = models.Range.objects.create(
            name="category range", includes_all_services=False
        )
        cat_range.included_categories.add(parent_category)
        ranges = models.Range.objects.contains_service(self.parent)
        self.assertEqual(
            ranges.count(),
            2,
            "Since the parent category is part of the range, There should be 2 "
            "ranges containing the parent service, which is in a subcategory",
        )
        self.assertIn(
            cat_range,
            ranges,
            "The range containing the parent category of the parent service, should be selected",
        )

        ranges = models.Range.objects.contains_service(self.child1)
        self.assertEqual(
            ranges.count(),
            3,
            "Since the parent category is part of the range, There should be 3 "
            "ranges containing the child service, which is in a subcategory",
        )
