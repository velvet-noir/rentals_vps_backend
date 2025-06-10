from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Service
from .serializers import (
    ServiceDetailSerializer,
    ServiceSerializer,
)


class ServiceList(APIView):
    model_class = Service
    serializer_class = ServiceSerializer

    @swagger_auto_schema(
        operation_summary="Получить список всех серверов",
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

    @swagger_auto_schema(
        operation_summary="Создать новый сервер",
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
