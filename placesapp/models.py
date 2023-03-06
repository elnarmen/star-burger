from django.db import models
from django.utils import timezone
from django.conf import settings


class Place(models.Model):
    address = models.CharField('Адрес', max_length=255, unique=True)
    longitude = models.DecimalField(
        'Долгота',
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True
    )
    latitude = models.DecimalField(
        'Широта',
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True
    )
    update_at = models.DateTimeField('Дата последнего обновления', default=timezone.now)

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.address
