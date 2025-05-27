from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Q
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.models import (
    Application,
    ApplicationService,
    ApplicationStatus,
    Service,
    ServiceSpecification,
)
from api.serializers import (
    ApplicationSerializer,
    ServiceDetailSerializer,
    ServiceSerializer,
    ServiceSpecSerializer,
)


class ServiceList(APIView):
    model_class = Service
    serializer_class = ServiceSerializer

    @swagger_auto_schema(
        operation_summary="Получить список сервисов",
        operation_description="Возвращает список всех активных сервисов. Можно фильтровать по query параметру.",
        responses={200: ServiceSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Фильтр по имени или описанию",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def get(self, request, format=None):
        try:
            query = request.query_params.get("query", "")
            services = self.model_class.objects.filter(is_active=True)

            if query:
                services = services.filter(
                    Q(name__icontains=query) | Q(mini_description__icontains=query)
                ).distinct()

            serializer = self.serializer_class(services, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Создать новый сервис",
        request_body=ServiceSerializer,
        responses={201: ServiceSerializer},
    )
    def post(self, request, format=None):
        try:
            serializer = self.serializer_class(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"status": "error", "mesdetailsage": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceDetail(APIView):
    model_class = Service
    serializer_class = ServiceDetailSerializer

    @swagger_auto_schema(
        operation_summary="Получить детали сервиса",
        tags=["Сервисы - Детали"],
        responses={200: ServiceDetailSerializer},
    )
    def get(self, request, pk, format=None):
        try:
            service = get_object_or_404(self.model_class, pk=pk, is_active=True)
            serializer = self.serializer_class(service)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Частично обновить сервис",
        request_body=ServiceDetailSerializer,
        responses={200: ServiceDetailSerializer},
    )
    def patch(self, request, pk, format=None):
        try:
            service = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(service, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Удалить сервис (деактивация)", responses={204: "No Content"}
    )
    def delete(self, request, pk, format=None):
        try:
            service = get_object_or_404(self.model_class, pk=pk)

            if not service.is_active:
                return Response(
                    {"detail": "Service already deleted"}, status=status.HTTP_410_GONE
                )

            service.is_active = False
            service.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceSpecList(APIView):
    model_class = ServiceSpecification
    serializer_class = ServiceSpecSerializer

    @swagger_auto_schema(
        operation_summary="Получить список спецификаций сервисов",
        responses={200: ServiceSpecSerializer(many=True)},
    )
    def get(self, request, format=None):
        try:
            specs = self.model_class.objects.all().select_related("service")

            serializer = self.serializer_class(specs, many=True)

            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Создать новую спецификацию сервиса",
        request_body=ServiceSpecSerializer,
        responses={201: ServiceSpecSerializer},
    )
    def post(self, request, format=None):
        try:
            serializer = self.serializer_class(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()

            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceSpecDetail(APIView):
    model_class = ServiceSpecification
    serializer_class = ServiceSpecSerializer

    @swagger_auto_schema(
        operation_summary="Получить характеристики услуги",
        responses={200: ServiceSpecSerializer},
    )
    def get(self, request, pk, format=None):
        try:
            spec = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(spec)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Частично обновить характеристики",
        request_body=ServiceSpecSerializer,
        responses={200: ServiceSpecSerializer},
    )
    def patch(self, request, pk, format=None):
        try:
            spec = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(spec, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(
                    {"status": "error", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    swagger_auto_schema(
        operation_summary="Удалить характеристики", responses={204: "No Content"}
    )

    def delete(self, request, pk, format=None):
        try:
            spec = get_object_or_404(self.model_class, pk=pk)
            spec.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "detail": f"Failed to delete specification: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplicationList(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer

    @swagger_auto_schema(
        operation_summary="Получить список заявок",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Фильтр по статусу заявки (ID)",
                type=openapi.TYPE_INTEGER,
            )
        ],
        responses={200: ApplicationSerializer(many=True)},
    )
    def get(self, request, format=None):
        try:
            applications = self.model_class.objects.exclude(
                Q(status__name="draft") | Q(status__name="deleted")
            ).select_related("status")

            status_id = request.query_params.get("status")
            if status_id:
                applications = applications.filter(status__id=status_id)

            serializer = self.serializer_class(applications, many=True)

            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplicationDetail(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer

    @swagger_auto_schema(
        operation_summary="Получить детали заявки",
        responses={200: ApplicationSerializer},
    )
    def get(self, request, pk, format=None):
        try:
            application = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(application)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Сменить статус заявки на 'Сформирована'",
        responses={200: ApplicationSerializer},
    )
    def put(self, request, pk, format=None):
        try:
            application = get_object_or_404(
                self.model_class.objects.select_related("status"), pk=pk
            )

            if application.status_id == 2:
                return Response(
                    {"detail": "The application already has the status of 'Formed'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            formed_status = get_object_or_404(ApplicationStatus, pk=2)
            application.status = formed_status
            application.save()

            serializer = self.serializer_class(application)
            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                    "detail": "The application status has been successfully changed to 'Formed'",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Сменить статус заявки на 'Удалена'",
        responses={200: ApplicationSerializer},
    )
    def delete(self, request, pk, format=None):
        try:
            application = get_object_or_404(
                self.model_class.objects.select_related("status"), pk=pk
            )

            if application.status_id == 5:
                return Response(
                    {"detail": "The application has already been marked as deleted"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            deleted_status = get_object_or_404(ApplicationStatus, pk=5)
            application.status = deleted_status
            application.save()

            serializer = self.serializer_class(application)
            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                    "detail": "The application has been successfully marked as deleted",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RemoveServiceFromApplicationView(APIView):
    @swagger_auto_schema(
        operation_summary="Удалить сервис из заявки", responses={204: "No Content"}
    )
    def delete(self, request, applic_id, service_id, format=None):
        try:
            app_service = get_object_or_404(
                ApplicationService.objects.select_related("application", "service"),
                application_id=applic_id,
                service_id=service_id,
            )

            app_service.delete()

            return Response(
                {
                    "status": "success",
                    "detail": "The service was successfully removed from the application.",
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
