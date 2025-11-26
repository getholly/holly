from django.contrib.sitemaps import Sitemap

from .models import RepositoryDetail


class RepositoryDetailSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        return RepositoryDetail.objects.filter(private=False)

    def lastmod(self, obj):
        return obj.updated_at
