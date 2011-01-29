from django.http import HttpResponse


class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401


class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = 503

