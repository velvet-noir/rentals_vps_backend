from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Application, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "image",
            "mini_description",
            "price",
            "is_active",
        ]


class ServiceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    services = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "pk",
            "status",
            "created_at",
            "updated_at",
            "user_creator",
            "user_moderator",
            "services",
        ]

    def get_services(self, obj):
        app_services = obj.services.all()
        services = [app_service.service for app_service in app_services]
        return ServiceSerializer(services, many=True).data


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
