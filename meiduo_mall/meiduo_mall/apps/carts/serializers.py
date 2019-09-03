from rest_framework import serializers

from goods.models import SKU

class CartSerializer(serializers.Serializer):
    """购物车参数"""
    sku_id = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(min_value=1)
    selected = serializers.BooleanField(default=True)

    def validate(self, attrs):
        sku_id = attrs['sku_id']
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        # 判断库存
        count = attrs['count']
        if sku.stock < count:
            raise serializers.ValidationError('商品库存不足')

        return attrs


class CartSKUSerializer(serializers.ModelSerializer):
    """购物车结算界面序列化器"""
    count = serializers.IntegerField()
    selected = serializers.BooleanField()

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count', 'selected')

class CartDeleteSerializer(serializers.Serializer):
    """购物车删除商品序列化器"""
    sku_id = serializers.IntegerField(min_value=1)

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value
