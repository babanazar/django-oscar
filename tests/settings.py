import os

from oscar.defaults import *  # noqa

# Path helper
location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

ALLOWED_HOSTS = ['test', '.oscarcommerce.com']

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DATABASE_NAME', 'oscar'),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', None),
        'HOST': os.environ.get('DATABASE_HOST', ''),
        'PORT': os.environ.get('DATABASE_PORT', 5432),
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    'sandbox.oscar.config.Shop',
    'sandbox.oscar.apps.analytics.apps.AnalyticsConfig',
    'sandbox.oscar.apps.checkout.apps.CheckoutConfig',
    'sandbox.oscar.apps.address.apps.AddressConfig',
    'sandbox.oscar.apps.shipping.apps.ShippingConfig',
    'sandbox.oscar.apps.catalogue.apps.CatalogueConfig',
    'sandbox.oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'sandbox.oscar.apps.communication.apps.CommunicationConfig',
    'sandbox.oscar.apps.partner.apps.PartnerConfig',
    'sandbox.oscar.apps.basket.apps.BasketConfig',
    'sandbox.oscar.apps.payment.apps.PaymentConfig',
    'sandbox.oscar.apps.offer.apps.OfferConfig',
    'sandbox.oscar.apps.order.apps.OrderConfig',
    'sandbox.oscar.apps.customer.apps.CustomerConfig',
    'sandbox.oscar.apps.search.apps.SearchConfig',
    'sandbox.oscar.apps.voucher.apps.VoucherConfig',
    'sandbox.oscar.apps.wishlists.apps.WishlistsConfig',
    'sandbox.oscar.apps.dashboard.apps.DashboardConfig',
    'sandbox.oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'sandbox.oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'sandbox.oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'sandbox.oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'sandbox.oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'sandbox.oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'sandbox.oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'sandbox.oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'sandbox.oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'sandbox.oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'sandbox.oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'sandbox.oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    # 3rd-party apps that oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'easy_thumbnails',
    'django_tables2',

    # Contains models we need for testing
    'tests._site.model_tests_app',
    'tests._site.myauth',
]

# Use a custom partner app to test overriding models. I can't find a way of
# doing this on a per-test basis, so I'm using a global change.
partner_app_idx = INSTALLED_APPS.index('oscar.apps.partner.apps.PartnerConfig')
INSTALLED_APPS[partner_app_idx] = 'tests._site.apps.partner.apps.PartnerConfig'
customer_app_idx = INSTALLED_APPS.index('oscar.apps.customer.apps.CustomerConfig')
INSTALLED_APPS[customer_app_idx] = 'tests._site.apps.customer.apps.CustomerConfig'
catalogue_app_idx = INSTALLED_APPS.index('oscar.apps.catalogue.apps.CatalogueConfig')
INSTALLED_APPS[catalogue_app_idx] = 'tests._site.apps.catalogue.apps.CatalogueConfig'
dashboard_app_idx = INSTALLED_APPS.index('oscar.apps.dashboard.apps.DashboardConfig')
INSTALLED_APPS[dashboard_app_idx] = 'tests._site.apps.dashboard.apps.DashboardConfig'
checkout_app_idx = INSTALLED_APPS.index('oscar.apps.checkout.apps.CheckoutConfig')
INSTALLED_APPS[checkout_app_idx] = 'tests._site.apps.checkout.apps.CheckoutConfig'

AUTH_USER_MODEL = 'myauth.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('_site/templates'),
        ],
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                'sandbox.oscar.apps.search.context_processors.search_form',
                'sandbox.oscar.apps.communication.notifications.context_processors.notifications',
                'sandbox.oscar.apps.checkout.context_processors.checkout',
                'sandbox.oscar.core.context_processors.metadata',
            ]
        }
    }
]


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'sandbox.oscar.apps.basket.middleware.BasketMiddleware',
]


AUTHENTICATION_BACKENDS = (
    'sandbox.oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

HAYSTACK_CONNECTIONS = {'default': {'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ROOT_URLCONF = 'tests._site.urls'
LOGIN_REDIRECT_URL = '/accounts/'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
PUBLIC_ROOT = location('public')
MEDIA_ROOT = os.path.join(PUBLIC_ROOT, 'media')
DEBUG = False
SITE_ID = 1
USE_TZ = 1
APPEND_SLASH = True
DDF_DEFAULT_DATA_FIXTURE = 'tests.dynamic_fixtures.OscarDynamicDataFixtureClass'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
LANGUAGE_CODE = 'en-gb'

OSCAR_INITIAL_ORDER_STATUS = 'A'
OSCAR_ORDER_STATUS_PIPELINE = {'A': ('B',), 'B': ()}
OSCAR_INITIAL_LINE_STATUS = 'a'
OSCAR_LINE_STATUS_PIPELINE = {'a': ('b', ), 'b': ()}

SECRET_KEY = 'notverysecret'
# Removed in Django 4.0, then we need to update the hashes to SHA-256 in tests/integration/order/test_models.py
DEFAULT_HASHING_ALGORITHM = 'sha1'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
FIXTURE_DIRS = [location('unit/fixtures')]
