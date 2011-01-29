import time

from django.test import TestCase
from django.test.client import MULTIPART_CONTENT


class BaseTestCase(TestCase):
    def get_200(self, url, data={}, follow=False):
        """
        request url with self.client and test that response status code = 200
        """
        response = self.client.get(url, data, follow)
        self.assertEquals(response.status_code, 200)
        return response

    def post_200(self, url, data={}, content_type=MULTIPART_CONTENT,
             follow=False, **extra):
        """
        requests url with self.client via POST
        and test that response status code is 200
        """
        response = self.client.post(url, data, content_type, follow, **extra)
        self.assertEquals(response.status_code, 200)
        return response

    def assertIterableEquals(self, first, second, assertOrder=False):
        self.assertEqual(len(first), len(second), "Iterable's length are not equal \n%s \n!= \n%s" % (first,second))

        equal = True
        for idx in xrange(len(first)):
            if assertOrder:
                equal = first[idx] == second[idx]
            else:
                equal = first[idx] in second
            if not equal:
                break
        self.assertTrue(equal, "Iterable not equal \n%s \n!= \n%s" % (first,second))

    def assertDictEquals(self, first, second):
        """ Asserts that keys from first are present in second and their values
        are equal. first MUST be iterable, second not.

        """
        for key in first:
            if hasattr(second, "__getitem__"):
                self.assert_(second.has_key(key), "Second dict has no key '%s' (=='%s' in first)" %(key, first[key]))
                second_value = second[key]
            else:
                self.assert_(hasattr(second, key), "Second object has no attr '%s' (=='%s' in first)" %(key, first[key]))
                second_value = getattr(second, key)
            self.assertEqual(first[key], second_value, "Values for key %s not equals (%s,%s)" %(key, first[key], second_value))

    def sleepNotLessThan(self, delay):
        start = time.time()
        while time.time() - start < delay:
            time.sleep(max(delay/20.0, 0.05))
        return time.time() - start

    def sleep(self, delay):
        start = time.time()
        time.sleep(delay)
        return time.time() - start

