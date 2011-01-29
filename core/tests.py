# encoding: utf-8
import datetime
import random
import traceback
try:
    set
except NameError:
    from sets import Set as set

import django.test
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, get_resolver
from django.http import HttpResponse

from core.auth.utils import get_unique_username
from core.cache.utils import cache_page
from core.decorators import limit_request_rate
from core.paginator import CompoundPaginator
from core.test import BaseTestCase
from core.utils import clear_cache, get_decorated_function
from core.auth import utils


# tests from other places
from utils.tests import *
# /tests from other places


urlpatterns = patterns('',
    (r'^$', 'core.tests.simple_view'),
    (r'^view2$', 'core.tests.simple_view1'),
    (r'^obj_id$', 'core.tests.simple_view_o'),
    (r'^obj_id2$', 'core.tests.simple_view_o1'),
    (r'^finduser', 'core.views.find_user.find_user'),
)

RATELIMIT = 2

@limit_request_rate(RATELIMIT)
def simple_view(request):
    return HttpResponse('ok')

@limit_request_rate()
def simple_view1(request):
    return HttpResponse('ok1')

@limit_request_rate(RATELIMIT, object_id='svo')
def simple_view_o(request):
    return HttpResponse('ok')

@limit_request_rate(object_id='svo1')
def simple_view_o1(request):
    return HttpResponse('ok1')

class LimitRequestRateTestCase(BaseTestCase):
    urls = 'core.tests'

    url1 = '/'
    url2 = '/view2'

    users_data = [{'username':'alice', 'password':'secret', 'email':'alice@example.com'},
                  {'username':'bob', 'password':'secret', 'email':'bob@example.com'}]
    def setUp(self):
        self.sample_user = User.objects.create_user(**self.users_data[0])
        self.sample_user2 = User.objects.create_user(**self.users_data[1])

        clear_cache()

    def login(self, user_id):
        self.assertTrue(self.client.login(username=self.users_data[user_id]['username'], password=self.users_data[user_id]['password']))

    def test_anonymous(self):
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)

    def test_limit(self):
        self.login(0)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 503)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 503)

    def test_diff_users(self):
        self.login(0)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)
        self.login(1)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)

    def test_diff_functions(self):
        self.login(0)

        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)

        response = self.client.get(self.url2)
        self.assertEquals(response.status_code, 200)

    def test_after_limit(self):
        self.login(0)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)
        # Add one second due to memcached expire precision.
        self.sleepNotLessThan(RATELIMIT + 1)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)

    def test_middle_limit(self):
        self.login(0)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 200)
        self.sleep(RATELIMIT/2.0)
        response = self.client.get(self.url1)
        self.assertEquals(response.status_code, 503)


class LimitRequestRateObjectIdTestCase(LimitRequestRateTestCase):
    url1 = '/obj_id'
    url2 = '/obj_id2'


class GetDecorationFunctionTestCase(BaseTestCase):
    def dummy_decorator(self, function):
        def actual_decorator():
            return function()
        return actual_decorator

    def tf(self):
        pass

    def dassert(self, func):
        self.assertEquals(get_decorated_function(func), self.tf)

    def test(self):
        self.dassert(self.tf)
        df = self.tf
        for x in xrange(5):
            df = self.dummy_decorator(df)
            self.dassert(df)


class AuthTestCase(BaseTestCase):
    def test_get_unique_username(self):
        base_name = 'username'

        username = get_unique_username(base_name)
        self.assertEquals(username, base_name)

        user = User.objects.create_user(username, 'username@example.com', '12345')
        username = get_unique_username(base_name)
        self.assertEquals(username, ''.join((base_name, '1')))

        user = User.objects.create_user(username, 'username1@example.com', '12345')
        username = get_unique_username(base_name)
        self.assertEquals(username, ''.join((base_name, '2')))


class FindUserTestCase(BaseTestCase):
    urls = 'core.tests'

    users_data = [
        {'username':'alice', 'password':'secret', 'email':'alice@example.com'},
        {'username':'aliceInChains', 'password':'secret', 'email':'aliceInChains@example.com'},
        {'username':'aliceInTheMirrorLand_o_O', 'password':'secret', 'email':'aliceInTheMirrorLand_o_O@example.com'},
        {'username':'bob', 'password':'secret', 'email':'bob@example.com'},
    ]

    def setUp(self):
        self.users = {}
        for user in self.users_data:
            self.users[user['username']] = User.objects.create_user(**user)

    def login(self, user_id):
        self.assertTrue(self.client.login(username=self.users_data[user_id]['username'], password=self.users_data[user_id]['password']))

    def search(self, q):
        return self.get_200(reverse('core.views.find_user.find_user'), {'q': q})

    def test_none_found(self):
        self.login(0)
        response = self.search('I\'m looking for the truth')
        self.assertEquals(response.content, '')

    def test_only_a_found(self):
        self.login(3)
        response = self.search('a')
        users = response.content.split('\n')
        correct_users = ('alice', 'aliceInChains', 'aliceInTheMirrorLand_o_O')
        self.assertIterableEquals(users, correct_users)

    def test_self_not_found(self):
        self.login(0)
        response = self.search('a')
        users = response.content.split('\n')
        correct_users = ('aliceInChains', 'aliceInTheMirrorLand_o_O')
        self.assertIterableEquals(users, correct_users)


class CompoundPaginatorTestCase(BaseTestCase):
    def test_basic(self):
        p = CompoundPaginator((range(0,20), range(20, 50)), 5)
        for page_n in p.page_range:
            page = p.page(page_n)
            self.assertIterableEquals(range(5 * (page_n - 1), 5 * page_n), page.object_list)

    def test_boundary(self):
        onpage = 5
        p = CompoundPaginator((range(1), range(1, 50)), onpage)
        for page_n in p.page_range:
            page = p.page(page_n)
            self.assertIterableEquals(range(onpage * (page_n - 1), onpage * page_n), page.object_list)

        p = CompoundPaginator((range(39), range(39, 40)), onpage)
        for page_n in p.page_range:
            page = p.page(page_n)
            self.assertIterableEquals(page.object_list, range(onpage * (page_n - 1), onpage * page_n))

    def test_qs(self):
        for n in xrange(10, 20):
            name = 'u%d' % n
            user = User.objects.create(username=name, is_active=True)
        for n in xrange(20, 30):
            name = 'u%d' % n
            user = User.objects.create(username=name, is_active=False)

        onpage = 2
        p = CompoundPaginator((User.objects.filter(is_active=True), User.objects.filter(is_active=False)), onpage)
        for page_n in p.page_range:
            page = p.page(page_n)
            self.assertIterableEquals(range(onpage * (page_n - 1) + 10, onpage * page_n + 10),
                                      [int(user.username[1:]) for user in page.object_list])

        p = CompoundPaginator(([User.objects.get(username='u20')], User.objects.filter(is_active=False).exclude(username='u20')), onpage)
        for page_n in p.page_range:
            page = p.page(page_n)
            self.assertIterableEquals(range(onpage * (page_n - 1) + 20, onpage * page_n + 20),
                                      [int(user.username[1:]) for user in page.object_list])

        p = CompoundPaginator((User.objects.filter(username='u20'), User.objects.filter(username='u21')), onpage)
        page = p.page(1)
        self.assertIterableEquals([User.objects.get(username='u20'), User.objects.get(username='u21')], page.object_list)


PAGE_CACHE_TIME = 2

@cache_page(PAGE_CACHE_TIME)
def cache_page_view(request):
    return HttpResponse(str(random.random()))

urlpatterns += patterns('',
    (r'^cache_page_view$', 'core.tests.cache_page_view'),
)

class CachePageTestCase(BaseTestCase):
    urls = 'core.tests'

    users_data = [{'username':'alice', 'password':'secret', 'email':'alice@example.com'},
                  {'username':'bob', 'password':'secret', 'email':'bob@example.com'}]
    def setUp(self):
        self.sample_user = User.objects.create_user(**self.users_data[0])
        self.sample_user2 = User.objects.create_user(**self.users_data[1])

        clear_cache()

    def login(self, user_id):
        self.assertTrue(self.client.login(username=self.users_data[user_id]['username'], password=self.users_data[user_id]['password']))

    def test_different_users(self):
        response_anonymous =  self.get_200('/cache_page_view')
        self.login(0)
        response_1 = self.get_200('/cache_page_view')
        self.login(1)
        response_2 = self.get_200('/cache_page_view')
        response_2_1 = self.get_200('/cache_page_view')

        # Assert that only 3 responses are different
        self.assertEqual(len(set([response_anonymous.content,
                                  response_1.content,
                                  response_2.content,
                                  response_2_1.content])),
                             3)
        # And assert that only responses for same user are same
        self.assertEqual(response_2.content, response_2_1.content)

    def test_after_timeout(self):
        response = self.get_200('/cache_page_view')
        response2 = self.get_200('/cache_page_view')

        self.assertEqual(response.content, response2.content)
        self.sleepNotLessThan(PAGE_CACHE_TIME)
        self.sleepNotLessThan(1)
        response2 = self.get_200('/cache_page_view')
        self.assertNotEqual(response.content, response2.content)

    def test_after_small_timeout(self):
        response = self.get_200('/cache_page_view')
        response2 = self.get_200('/cache_page_view')

        self.assertEqual(response.content, response2.content)
        self.sleepNotLessThan(PAGE_CACHE_TIME/2)
        response2 = self.get_200('/cache_page_view')
        self.assertEqual(response.content, response2.content)

class CoreAuthUtils(BaseTestCase):
    def setUp(self):
        self.users = []
        self.users.append(User.objects.create_user(username='alice',
                                             email='alice@mailforspam.com',
                                             password='123123'))

        self.users.append(User.objects.create_user(username='alice1',
                                             email='alice1@mailforspam.com',
                                             password='123123'))

        self.users.append(User.objects.create_user(username='alices',
                                             email='alices@mailforspam.com',
                                             password='123123'))


    def test_conflicts_url(self):
        self.assertEqual(utils.conflicts_url('login'), True)
        self.assertEqual(utils.conflicts_url('login1'), False)

    def test_get_username_diff_from_url(self):
        self.assertEqual(utils.get_username_diff_from_url('login'), 'login1')
        self.assertEqual(utils.get_username_diff_from_url('login2'), 'login2')

    def test_get_unique_username(self):
        self.assertEqual(utils.get_unique_username(u'Анатолий Ларин'), 'Anatolij_Larin')
        self.assertEqual(utils.get_unique_username('alice'), 'alice2')
        self.assertEqual(utils.get_unique_username('alices'), 'alices1')
        self.assertEqual(utils.get_unique_username('login'), 'login1')
        self.assertEqual(utils.get_unique_username('ali'), 'ali')
        self.assertEqual(utils.get_unique_username('ali_$89*0890*&^%'), 'ali__89_0890')


class AllUrlsTestCase(BaseTestCase):
    def setUp(self):
        super(AllUrlsTestCase, self).setUp()

    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password=self.password))

    def test_non_500(self):
        for func, pattern in get_resolver(settings.ROOT_URLCONF).reverse_dict.items():
            url = pattern[0][0]
            # check param-less urls
            if not url[1]:
                try:
                    response = self.client.get('/' + url[0], follow=True)
                    self.assertNotEqual(response.status_code / 100, 5)
                except Exception,e:
                    self.fail('GET %s failed\n %s' % (url[0], traceback.format_exc()))
            else:
                params = {}
                for key in url[1]:
                    params[key] = 1
                fullurl = '/' + url[0] % params
                response = self.client.get(fullurl, follow=True)
                self.assertNotEqual(response.status_code / 100, 5, fullurl)

    def test_non_500_loggedin(self):
        self.password = '123123'
        self.user = User.objects.create_user(username='alice',
                                             email='alice@mailforspam.com',
                                             password=self.password)
        self.login(self.user)
        self.test_non_500()

    def test_post_non_500(self):
        for func, pattern in get_resolver(settings.ROOT_URLCONF).reverse_dict.items():
            url = pattern[0][0]
            # check param-less urls
            if not url[1]:
                try:
                    response = self.client.post('/' + url[0], follow=True)
                    self.assertNotEqual(response.status_code / 100, 5)
                except Exception,e:
                    self.fail('POST %s failed\n %s' % (url[0], traceback.format_exc()))

    def test_post_non_500_loggedin(self):
        self.password = '123123'
        self.user = User.objects.create_user(username='alice',
                                             email='alice@mailforspam.com',
                                             password=self.password)
        self.login(self.user)
        self.test_post_non_500()


class CopyrightYearsTestCase(django.test.TestCase):
    def default_test(self, param, expected):
        from core.templatetags.copyright import copyright_years
        self.assertEquals(copyright_years(param), expected)

    def test_current_year(self):
        self.default_test(datetime.date.today().year, datetime.date.today().year)

    def test_another_year_past(self):
        year = datetime.date.today().year - 5
        self.default_test(year, '%d&ndash;%d' % (year, datetime.date.today().year))

    def test_another_year_future(self):
        year = datetime.date.today().year + 5
        self.default_test(year, '%d&ndash;%d' % (datetime.date.today().year, year))

