from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest


@login_required
def find_user(request):
    if request.method == 'GET':
        q = request.GET.get('q', '')
        if len(q):
            users = User.objects.filter(username__istartswith=q).exclude(pk=request.user.pk)
            usernames = [user.username for user in users]
            return HttpResponse('\n'.join(usernames))

    return HttpResponseBadRequest()

