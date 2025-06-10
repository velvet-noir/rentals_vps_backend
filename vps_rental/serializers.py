from rest_framework import serializers
from .models import Application, Service, ServiceSpecification


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSpecification
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
