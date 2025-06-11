from django.contrib import admin

from .models import Application, ApplicationService, Service


class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "image", "price", "is_active")
    ordering = ("id",)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_status_name",
        "created_at",
        "updated_at",
        "user_creator",
        "user_moderator",
    )
    ordering = ("created_at",)

    def get_status_name(self, obj):
        return obj.get_status_display()

    get_status_name.short_description = "Status"


class ApplicationServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "get_service_name")

    def get_service_name(self, obj):
        return f"Характеристика: {obj.service.name}"


admin.site.register(Service, ServiceAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationService, ApplicationServiceAdmin)
