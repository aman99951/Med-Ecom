from rest_framework import serializers
from .models import *
from django.contrib.auth import authenticate


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['name']  # You can add more fields if needed


class VariantSerializer(serializers.ModelSerializer):
    unit = UnitSerializer(read_only=True)

    class Meta:
        model = Variant
        fields = ['id', 'unit', 'potency', 'number_of_tablets',
                  'price_inr', 'price_usd', 'manufacturer']


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand_name', 'type', 'sub_description', 'how_to_use',
                  'side_effects', 'drug_interactions', 'precautions', 'featured',
                  'sale', 'top_selling', 'is_active', 'variants', 'images']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'variant', 'discount_type',
                  'discount_value', 'start_date', 'end_date']


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'variant', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(
        source="user.email", read_only=True)  # Add user email

    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_email', 'session_key',
                  'discount_code', 'created_at', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])  # Extract items list
        cart = Cart.objects.create(**validated_data)

        # Create CartItem instances and associate them with the cart
        for item_data in items_data:
            CartItem.objects.create(cart=cart, **item_data)

        return cart


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=True)
    mobile = serializers.CharField(max_length=15, required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'mobile', 'password']

    def create(self, validated_data):
        # Create a new user with the provided data
        user = User.objects.create(
            username=validated_data['email'],  # Using email as username
            email=validated_data['email'],
            first_name=validated_data['name'],
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.save()

        # Save mobile number to profile
        Profile.objects.create(
            user=user, mobile=validated_data['mobile']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Authenticate the user
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError(
                "Invalid credentials, please try again.")

        attrs['user'] = user
        return attrs
