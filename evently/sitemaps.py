from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            "homeplan",
            "food_home",
            "activities_home",
            "eventful_home",
            "punguza_home",
            "students_home",
        ]

    def location(self, item):
        return reverse(item)