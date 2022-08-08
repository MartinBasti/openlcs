from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)

from mptt.models import MPTTModel, TreeForeignKey
from packages.models import Package


class Product(models.Model):
    """Red Hat products"""

    name = models.TextField(unique=True)
    display_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    family = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'products'

    def __str__(self):
        return self.name

    def add_release(self, name, version, notes=""):
        release, _ = self.release_set.update_or_create(
            name=name,
            version=version,
            defaults={
                "notes": notes,
            },
        )
        return release


class Release(models.Model):
    """releases of each product"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.TextField()
    # 'name' is a joint string: product-version
    name = models.TextField()
    notes = models.TextField(blank=True, null=True)
    release_nodes = GenericRelation(
        "products.ProductTreeNode", related_query_name="release"
    )

    class Meta:
        app_label = 'products'
        unique_together = (('product', 'version'),)
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'version'], name='unique_product_version'
            )
        ]

    def __str__(self):
        return self.name

    def update_packages(self, nvr_list, is_source=True):
        existed_nvrs = self.packages.values_list('package_nvr', flat=True)
        nvrs = list(set(nvr_list) - set(existed_nvrs))
        objs = [
            ReleasePackage(release=self, package_nvr=nvr, is_source=is_source)
            for nvr in nvrs
        ]
        ReleasePackage.objects.bulk_create(objs)


class ReleasePackage(models.Model):
    """packages within each release"""

    release = models.ForeignKey(
        Release, related_name="packages", on_delete=models.CASCADE
    )
    package_nvr = models.TextField()
    is_source = models.BooleanField(
        default=True, help_text='True if the package is for source package'
    )

    class Meta:
        app_label = 'products'
        constraints = [
            models.UniqueConstraint(
                fields=['release', 'package_nvr'],
                name='unique_release_package_nvr',
            )
        ]

    def __str__(self):
        return "%s-%s" % (self.release, self.package_nvr)

    def get_scan_result(self):
        qs = Package.objects.filter(nvr=self.package_nvr).select_related()
        data = {}
        if qs.exists():
            package = qs[0]
            data.update({'sum_license': package.sum_license})
            if package.is_source:
                source = package.source
                licenses = (
                    source.get_license_detections()
                    .values_list('license_key', flat=True)
                    .distinct()
                )
                copyrights = (
                    source.get_copyright_detections()
                    .values_list('statement', flat=True)
                    .distinct()
                )
                data.update(
                    {
                        'url': source.url,
                        'licenses': licenses,
                        'copyrights': copyrights,
                    }
                )
        return data


class MpttTreeNodeMixin(MPTTModel):
    name = models.TextField()
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True


class ComponentTreeNode(MpttTreeNodeMixin):
    """Class representing the component tree."""

    def __str__(self):
        return f'{self.content_object.type} node: {self.name}'


class ProductTreeNode(MpttTreeNodeMixin):
    """Class representing the product tree."""

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'object_id'],
                name='unique_parent_content_object',
            )
        ]

    def __str__(self):
        if hasattr(self.content_object, 'type'):
            return f'{self.content_object.type} node: {self.name}'
        return f'Product node: {self.name}'
