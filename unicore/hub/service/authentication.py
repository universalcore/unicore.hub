import re

from zope.interface import implementer
from pyramid.interfaces import IAuthenticationPolicy


@implementer(IAuthenticationPolicy)
class PathAuthenticationPolicy(object):
    """ Pyramid authentication policy to use different policies per path
    """

    def __init__(self, path_map, default):
        self._path_map = map(lambda t: [t[0], t[1]], path_map)
        self._default = default
        self._path_info_cache = {}

    def _resolve_policy(self, path):
        for i, (path_re, policy) in enumerate(self._path_map):
            # calling compile with a pattern object returns
            # the provided pattern object
            path_re_compiled = re.compile(path_re)
            self._path_map[i][0] = path_re_compiled

            if path_re_compiled.match(path):
                return policy

        return self._default

    def get_active_policy(self, request):
        path = request.path_info

        if path not in self._path_info_cache:
            self._path_info_cache[path] = self._resolve_policy(path)

        return self._path_info_cache[path]

    def authenticated_userid(self, request):
        return self.get_active_policy(
            request).authenticated_userid(request)

    def unauthenticated_userid(self, request):
        return self.get_active_policy(
            request).unauthenticated_userid(request)

    def effective_principals(self, request):
        return self.get_active_policy(
            request).effective_principals(request)

    def remember(self, request, principal, **kw):
        return self.get_active_policy(
            request).remember(request, principal, **kw)

    def forget(self, request):
        return self.get_active_policy(
            request).forget(request)
