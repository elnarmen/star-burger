from rest_framework.serializers import ModelSerializer
from .models import Order, OrderProduct
from placesapp.location_utils import save_place


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']

    def create(self, validated_data):
        product_items = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        save_place(order.address)
        order_products = [OrderProduct(
            order=order,
            price=product_item['product'].price,
            product=product_item['product'],
            quantity=product_item['quantity']
        ) for product_item in product_items]

        OrderProduct.objects.bulk_create(order_products)
        return order
