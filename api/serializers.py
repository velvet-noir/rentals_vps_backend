from rest_framework import serializers
from .models import (
    Application,
    ApplicationService,
    ApplicationStatus,
    Service,
    ServiceSpecification,
)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSpecification
        fields = "__all__"


class ServiceDetailSerializer(serializers.ModelSerializer):
    specifications = ServiceSpecSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            "pk",
            "name",
            "image",
            "mini_description",
            "price",
            "is_active",
            "specifications",
        ]


class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatus
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    status = ApplicationStatusSerializer(read_only=True)
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
        services = Service.objects.filter(applications__application=obj)
        return ServiceSerializer(services, many=True).data


class ApplicationServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationService
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "password")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if user and user.is_active:
            data["user"] = user
            return data
        raise serializers.ValidationError("Неверные данные для входа")
