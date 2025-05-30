from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

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
    LoginSerializer,
    RegisterSerializer,
    ServiceDetailSerializer,
    ServiceSerializer,
    ServiceSpecSerializer,
)


def is_moderator(user):
    return user.is_authenticated and user.is_staff and not user.is_superuser


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


class ServiceList(APIView):
    model_class = Service
    serializer_class = ServiceSerializer

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить список всех услуг",
        responses={200: ServiceSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Фильтр по имени или описанию",
                type=openapi.TYPE_STRING,
            ),
        ],
        tags=["services/"],
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
        operation_summary="Создать новую услугу",
        request_body=ServiceSerializer,
        responses={201: ServiceSerializer},
        tags=["services/"],
    )
    def post(self, request, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

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
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceDetail(APIView):
    model_class = Service
    serializer_class = ServiceDetailSerializer

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить одну услугу по ID с характеристиками",
        responses={200: ServiceDetailSerializer},
        tags=["services/{id}/"],
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
        operation_summary="Обновить одну услугу по ID",
        request_body=ServiceDetailSerializer,
        responses={200: ServiceDetailSerializer},
        tags=["services/{id}/"],
    )
    def patch(self, request, pk, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

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
        except Exception:
            return Response(
                {"status": "error", "detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Удалить(через статус) одну услугу по ID",
        responses={204: "No Content"},
        tags=["services/{id}/"],
    )
    def delete(self, request, pk, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = get_object_or_404(self.model_class, pk=pk)
            if not service.is_active:
                return Response(
                    {"detail": "Service already deleted"}, status=status.HTTP_410_GONE
                )

            service.is_active = False
            service.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceSpecList(APIView):
    model_class = ServiceSpecification
    serializer_class = ServiceSpecSerializer

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить список всех характеристик",
        responses={200: ServiceSpecSerializer(many=True)},
        tags=["spec/"],
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
        operation_summary="Добавить новую характеристику",
        request_body=ServiceSpecSerializer,
        responses={201: ServiceSpecSerializer},
        tags=["spec/"],
    )
    def post(self, request, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

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

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить характеристику по ID",
        responses={200: ServiceSpecSerializer},
        tags=["spec/{id}/"],
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
        operation_summary="Обновить характеристику по ID",
        request_body=ServiceSpecSerializer,
        responses={200: ServiceSpecSerializer},
        tags=["spec/{id}/"],
    )
    def patch(self, request, pk, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

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
        except Exception:
            return Response(
                {"status": "error", "detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Удалить характеристику по ID",
        responses={204: "No Content"},
        tags=["spec/{id}/"],
    )
    def delete(self, request, pk, format=None):
        user = request.user
        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

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

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить список всех заявок",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Фильтр по имени статуса заявки",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: ApplicationSerializer(many=True)},
        tags=["applic/"],
    )
    def get(self, request, format=None):
        user = request.user
        try:
            if is_moderator(user) or is_superuser(user):
                applications = self.model_class.objects.exclude(
                    Q(status__name="draft") | Q(status__name="deleted")
                ).select_related("status")
            else:
                applications = (
                    self.model_class.objects.filter(user_creator=user)
                    .exclude(Q(status__name="draft") | Q(status__name="deleted"))
                    .select_related("status")
                )

            status_name = request.query_params.get("status")
            if status_name:
                applications = applications.filter(status__name=status_name)

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

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить одну заявку по ID",
        responses={200: ApplicationSerializer},
        tags=["applic/{id}/"],
    )
    def get(self, request, pk, format=None):
        user = request.user
        try:
            application = get_object_or_404(self.model_class, pk=pk)

            if not (
                is_moderator(user)
                or is_superuser(user)
                or application.user_creator == user
            ):
                return Response(
                    {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                )

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
        operation_summary="Установить для заявки статус 'formed(сформирована)'",
        responses={200: ApplicationSerializer},
        tags=["applic/{id}/"],
    )
    def put(self, request, pk, format=None):
        user = request.user
        try:
            application = get_object_or_404(
                self.model_class.objects.select_related("status"), pk=pk
            )

            if not (
                is_moderator(user)
                or is_superuser(user)
                or application.user_creator == user
            ):
                return Response(
                    {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
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

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Удалить заявку через смену статсуса на 'deleted(удалена)'",
        responses={200: ApplicationSerializer},
        tags=["applic/{id}/"],
    )
    def delete(self, request, pk, format=None):
        user = request.user
        try:
            application = get_object_or_404(
                self.model_class.objects.select_related("status"), pk=pk
            )

            if not (
                is_moderator(user)
                or is_superuser(user)
                or application.user_creator == user
            ):
                return Response(
                    {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
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
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Удаление сервиса по ID из заявки",
        responses={204: "No Content"},
        tags=["applic/{applic_id}/service/{service_id}"],
    )
    def delete(self, request, applic_id, service_id, format=None):
        user = request.user
        try:
            app_service = get_object_or_404(
                ApplicationService.objects.select_related("application", "service"),
                application_id=applic_id,
                service_id=service_id,
            )

            if not (
                is_moderator(user)
                or is_superuser(user)
                or app_service.application.user_creator == user
            ):
                return Response(
                    {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
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


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        request_body=RegisterSerializer,
        responses={201: RegisterSerializer},
        tags=["auth/"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response(
                {"status": "success", "message": "User created and logged in."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Авторизация пользователя",
        request_body=LoginSerializer,
        responses={201: LoginSerializer},
        tags=["auth/"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            return Response({"status": "success", "message": "Вход выполнен"})
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Выход из аккаунта пользователя",
        tags=["auth/"],
    )
    def post(self, request):
        logout(request)
        return Response(
            {"status": "success", "message": "Выход выполнен"},
            status=status.HTTP_200_OK,
        )


class DraftApplicationServiceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Добавить сервис в черновик заявки (создаст заявку, если её нет)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["service_id"],
            properties={
                "service_id": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={200: ApplicationSerializer},
        tags=["applic/draft/"],
    )
    def post(self, request):
        user = request.user
        service_id = request.data.get("service_id")

        if not service_id:
            return Response(
                {"detail": "service_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return Response(
                {"detail": "Service not found"}, status=status.HTTP_404_NOT_FOUND
            )

        draft_status = ApplicationStatus.objects.get(name="draft")
        application, created = Application.objects.get_or_create(
            user_creator=user, status=draft_status
        )

        if ApplicationService.objects.filter(
            application=application, service=service
        ).exists():
            return Response(
                {"detail": "Service already added"}, status=status.HTTP_400_BAD_REQUEST
            )

        ApplicationService.objects.create(application=application, service=service)

        serializer = ApplicationSerializer(application)
        return Response(
            {"status": "success", "data": serializer.data}, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Получить черновую заявку текущего пользователя, если есть",
        responses={200: ApplicationSerializer},
        tags=["applic/draft/"],
    )
    def get(self, request):
        user = request.user
        draft_status = ApplicationStatus.objects.get(name="draft")

        application = Application.objects.filter(
            user_creator=user, status=draft_status
        ).first()

        if not application:
            return Response(
                {"detail": "No draft application found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationSerializer(application)
        return Response(
            {"status": "success", "data": serializer.data}, status=status.HTTP_200_OK
        )


class ModeratorChangeStatusView(APIView):
    permission_classes = [IsAuthenticated]
    model_class = Application
    serializer_class = ApplicationSerializer

    @swagger_auto_schema(
        operation_summary="Модератор меняет статус заявки на accepted/completed/rejected",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status_id"],
            properties={
                "status_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID статуса: 3,4 или 6"
                ),
            },
        ),
        responses={200: ApplicationSerializer},
        tags=["applic/{id}/moderator_status/"],
    )
    def put(self, request, pk, format=None):
        user = request.user

        if not (is_moderator(user) or is_superuser(user)):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        status_id = request.data.get("status_id")
        if status_id not in [3, 4, 6]:
            return Response(
                {"detail": "Invalid status_id, allowed: 3,4,6"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = get_object_or_404(self.model_class, pk=pk)
            new_status = get_object_or_404(ApplicationStatus, pk=status_id)

            if application.status_id == status_id:
                return Response(
                    {"detail": "Application already has this status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            application.status = new_status
            application.user_moderator = user
            application.save()

            serializer = self.serializer_class(application)
            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                    "detail": f"Application status changed to '{new_status.name}' by moderator.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
