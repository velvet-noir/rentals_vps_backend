from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from .utils import redis_client

from .models import Application, ApplicationService, ApplicationStatus, Service
from .serializers import (
    ApplicationSerializer,
    LoginSerializer,
    RegisterSerializer,
    ServiceDetailSerializer,
    ServiceSerializer,
    UserSerializer,
)


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
        tags=["services"],
    )
    def get(self, request, format=None):
        try:
            query = request.query_params.get("query", "")
            services = self.model_class.objects.filter(is_active=True)

            if query:
                services = services.filter(Q(name__icontains=query)).distinct()

            serializer = self.serializer_class(services, many=True)
            return Response(
                {"status": "success", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ServiceAdd(APIView):
    model_class = Service
    serializer_class = ServiceDetailSerializer

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Создать новую услугу",
        request_body=ServiceDetailSerializer,
        responses={201: ServiceDetailSerializer},
        tags=["services"],
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
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceDetail(APIView):
    model_class = Service
    serializer_class = ServiceDetailSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        else:
            return [IsAdminUser()]

    @swagger_auto_schema(
        operation_summary="Получить один сервис по ID с характеристиками",
        responses={200: ServiceDetailSerializer},
        tags=["service"],
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
        operation_summary="Обновить один сервис по ID",
        request_body=ServiceDetailSerializer,
        responses={200: ServiceDetailSerializer},
        tags=["service"],
    )
    def put(self, request, pk, format=None):
        try:
            service = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(service, data=request.data)
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
        operation_summary="Удалить(через статус) один сервер по ID",
        responses={204: "No Content"},
        tags=["service"],
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
        except Exception:
            return Response(
                {"detail": "Internal server error"},
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
                description="Фильтр по статусу",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: ApplicationSerializer(many=True)},
        tags=["applications"],
    )
    def get(self, request, format=None):
        try:
            applications = self.model_class.objects.exclude(
                status__in=[ApplicationStatus.DRAFT, ApplicationStatus.DELETED]
            )

            if not request.user.is_staff:
                applications = applications.filter(user_creator=request.user)

            status_name = request.query_params.get("status")
            if status_name:
                applications = applications.filter(status=status_name)

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

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Получить одну заявку по ID",
        responses={200: ApplicationSerializer},
        tags=["application"],
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
        operation_summary="Модератор меняет статус заявки на completed/rejected",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={"status": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        responses={200: ApplicationSerializer},
        tags=["application"],
    )
    def put(self, request, pk, format=None):
        try:
            application = get_object_or_404(self.model_class, pk=pk)

            new_status = request.data.get("status")

            if new_status not in [
                ApplicationStatus.COMPLETED,
                ApplicationStatus.REJECTED,
            ]:
                return Response(
                    {"detail": "Invalid status. Allowed: COMPLETED or REJECTED."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            application.status = new_status
            application.save()

            serializer = self.serializer_class(application)
            return Response(
                {
                    "status": "success",
                    "data": serializer.data,
                    "detail": f"The application status has been successfully changed to '{new_status}'",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Удалить заявку через смену статуса на 'deleted'",
        responses={200: ApplicationSerializer},
        tags=["application"],
    )
    def delete(self, request, pk, format=None):
        try:
            application = get_object_or_404(self.model_class, pk=pk)

            application.status = ApplicationStatus.DELETED
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


class ApplicationFormed(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Установить для заявки статус 'formed(сформирована)'",
        responses={200: ApplicationSerializer},
        tags=["application/formed"],
    )
    def put(self, request, pk, format=None):
        try:
            application = get_object_or_404(self.model_class, pk=pk)

            if application.user_creator != request.user:
                return Response(
                    {"status": "error", "detail": "Нет доступа к этой заявке"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            application.status = ApplicationStatus.FORMED
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


class ApplicationDeleteServer(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Удаление сервиса по ID из черновой заявки пользователя",
        responses={204: "No Content"},
        tags=["application/delete-service"],
    )
    def delete(self, request, service_id, format=None):
        try:
            application = Application.objects.filter(
                user_creator=request.user, status=ApplicationStatus.DRAFT
            ).first()

            if not application:
                return Response(
                    {
                        "status": "error",
                        "detail": "Черновая заявка не найдена",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            app_service = get_object_or_404(
                ApplicationService,
                application=application,
                service_id=service_id,
            )

            if application.status != ApplicationStatus.DRAFT:
                return Response(
                    {
                        "status": "error",
                        "detail": "Удаление сервиса возможно только для заявок со статусом DRAFT.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            app_service.delete()
            return Response(
                {
                    "status": "success",
                    "detail": "Сервис успешно удалён из черновой заявки.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Информация о пользователе",
        responses={201: UserSerializer},
        tags=["user"],
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация пользователя",
        request_body=RegisterSerializer,
        responses={201: RegisterSerializer},
        tags=["user"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Пользователь зарегистрирован"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Авторизация пользователя",
        request_body=LoginSerializer,
        responses={201: LoginSerializer},
        tags=["user"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is not None:
            login(request, user)

            timestamp = datetime.now().isoformat()

            log_key = "auth:logins"
            log_entry = f'{user.username} logged in at {timestamp}'
            redis_client.lpush(log_key, log_entry)
            redis_client.ltrim(log_key, 0, 99)

            return Response({"message": "Вход выполнен"})
        else:
            return Response({"error": "Неверные данные"}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Выход пользователя",
        tags=["user"],
    )
    def post(self, request):
        logout(request)
        return Response({"message": "Выход выполнен"}, status=status.HTTP_200_OK)


class DraftApplicationServiceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Добавить услугу в черновик заявки (создаст заявку, если её нет)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["service_id"],
            properties={
                "service_id": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={200: ApplicationSerializer},
        tags=["application/draft"],
    )
    def post(self, request):
        user = request.user
        service_id = request.data.get("service_id")

        if not service_id:
            return Response(
                {"detail": "service_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = Service.objects.get(pk=service_id, is_active=True)
        except Service.DoesNotExist:
            return Response(
                {"detail": "Услуга не найдена или неактивна"},
                status=status.HTTP_404_NOT_FOUND,
            )

        application, _ = Application.objects.get_or_create(
            user_creator=user,
            status=ApplicationStatus.DRAFT,
        )

        if ApplicationService.objects.filter(
            application=application, service=service
        ).exists():
            return Response(
                {"detail": "Услуга уже добавлена в черновик"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ApplicationService.objects.create(application=application, service=service)

        serializer = ApplicationSerializer(application)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_summary="Получить черновую заявку текущего пользователя, если есть",
        responses={200: ApplicationSerializer},
        tags=["application/draft"],
    )
    def get(self, request):
        user = request.user

        application = Application.objects.filter(
            user_creator=user, status=ApplicationStatus.DRAFT
        ).first()

        if not application:
            return Response(
                {"detail": "Черновая заявка не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationSerializer(application)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )
