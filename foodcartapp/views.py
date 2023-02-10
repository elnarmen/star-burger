import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderProduct


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


@api_view(['POST'])
def register_order(request):
    try:
        decoded_response = request.data
    except ValueError:
        return Response({'error': 'bla bla bla'})
    if not decoded_response.get('products'):
        return Response(
            {'products': 'Обязательное поле.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if decoded_response['products'] is None:
        return Response(
            {'products': 'Это поле не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not isinstance(decoded_response['products'], list):
        return Response(
            {'products': 'Ожидался list со значениями, но был получен "str".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not len(decoded_response['products']):
        return Response(
            {'products': 'Этот список не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    order = Order.objects.create(
        firstname=decoded_response['firstname'],
        lastname=decoded_response['lastname'],
        phonenumber=decoded_response['phonenumber'],
        address=decoded_response['address']
    )
    order_products = [
        OrderProduct.objects.create(
            product=Product.objects.get(id=product['product']),
            quantity=product['quantity'],
            order=order
        ) for product in decoded_response['products']
    ]

