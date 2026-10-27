from django.shortcuts import redirect


class OldDomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        old_domain = "ukonangapi.onrender.com"
        host = request.get_host().split(":")[0].lower()

        if host == old_domain:
            new_url = (
                "https://ukonangapi.lol"
                + request.get_full_path()
            )
            return redirect(new_url, permanent=False)

        return self.get_response(request)