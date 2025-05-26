from rest_framework import serializers
from .models import (
    Application,
    ApplicationService,
    ApplicationStatus,
    Service,
    ServiceSpecification,
)


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
        fields = "__all__" + ("specifications",)


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
            "update_at",
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
