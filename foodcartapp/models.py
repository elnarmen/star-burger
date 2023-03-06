from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Prefetch
from django.conf import settings
from placesapp.models import Place
from placesapp.location_utils import fetch_coordinates


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('A', 'Необработан'),
        ('B', 'Передан в ресторан'),
        ('C', 'Передан курьеру'),
        ('D', 'Выполнен')
    )

    PAYMENT_METHOD_CHOICES = (
        ('C', 'Наличными'),
        ('E', 'Электронно'),
    )

    firstname = models.CharField(
        max_length=255,
        verbose_name='Имя',
        null=False,
        db_index=True
    )
    lastname = models.CharField(
        max_length=255,
        verbose_name='Фамилия',
        db_index=True
    )
    phonenumber = PhoneNumberField(verbose_name='номер телефона', db_index=True)
    address = models.CharField(
        max_length=255,
        verbose_name='Адрес',
        db_index=True
    )
    status = models.CharField(
        max_length=1,
        verbose_name='Статус',
        choices=STATUS_CHOICES,
        default='A',
        db_index=True
    )
    payment_method = models.CharField(
        max_length=1,
        verbose_name='Способ оплаты',
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True
    )
    creation_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Время создания',
        db_index=True

    )
    called_at = models.DateTimeField(
        verbose_name='Время звонка',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='Время доставки',
        blank=True,
        null=True,
        db_index=True
    )
    cooking_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Выбранный для приготовления ресторан',
        related_name='orders',
        on_delete=models.SET_NULL,
        default=None,
        blank=True,
        null=True
    )
    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address.split(", ")[0]}'

    def clean(self):
        if self.cooking_restaurant and self.status == 'A':
            self.status = 'B'

        place_coords = fetch_coordinates(
                settings.YANDEX_GEOCODER_API_KEY,
                self.address
            )

        place, _ = Place.objects.get_or_create(address=self.address)
        if not place_coords:
            place.latitude = place.longitude = None
            place.update_time = timezone.now()
            return
        place.latitude, place.longitude = place_coords
        place.save()


class OrderProduct(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name='продукт',
        on_delete=models.CASCADE,
        related_name='items'
    )
    quantity = models.IntegerField(
        verbose_name='количество',
        validators=[MinValueValidator(1)]
    )
    order = models.ForeignKey(
        Order,
        verbose_name='заказ',
        related_name='items',
        on_delete=models.CASCADE,
    )

    total_price = models.DecimalField(
        'цена для общего количества одинаковых продуктов',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'заказанный продукт'
        verbose_name_plural = 'заказанные продукты'

    def __str__(self):
        return f'{self.product} {self.quantity} шт.'

