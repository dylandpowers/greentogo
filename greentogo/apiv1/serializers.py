from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator

from core.models import Location, LocationTag, Restaurant, Subscription, User


class CheckinCheckoutSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[Location.CHECKIN, Location.CHECKOUT])
    location = serializers.CharField(max_length=6)
    subscription = serializers.IntegerField()
    number_of_boxes = serializers.IntegerField(min_value=1, default=1)

    def validate_location(self, value):
        try:
            location = Location.objects.get(code=value)
        except Location.DoesNotExist:
            raise ValidationError("Location does not exist.")
        return value

    def validate(self, data):
        location = Location.objects.get(code=data['location'])
        if location.service != data['action']:
            raise ValidationError("Invalid action for this location.")
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'name', 'available_boxes', 'max_boxes', )

    name = serializers.CharField(source="display_name")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('name', 'email', 'username', 'subscriptions', )

    subscriptions = SubscriptionSerializer(many=True)


class LocationTagSerializer(serializers.Serializer):
    subscription = serializers.IntegerField(source="subscription.id")
    location = serializers.CharField(source="location.code")
    service = serializers.CharField(source="location.service")
    available_boxes = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_available_boxes(self, obj):
        return obj.subscription.available_boxes


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ('name', 'address', 'latitude', 'longitude', 'phase')

    name = serializers.CharField()
    address = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    phase = serializers.IntegerField()
