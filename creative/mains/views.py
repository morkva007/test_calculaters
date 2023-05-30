from rest_framework import viewsets,status
from rest_framework.response import Response
from .models import (
    Calculater,
    S_directory_DCreative,
    Auditories,
    ChangeAuditories,
    Service,
    Accommodation
)
from rest_framework.validators import ValidationError
from .serializers import (
    CalculaterSerializer,
    S_directory_DCreativeSerializers,
    AuditoriesSerializers,
    ChangeAuditoriesSerializers,
    ServiceSerializers,
    AccommodationSerializers)


class S_directory_DCreativeViewSet(viewsets.ModelViewSet):
    queryset = S_directory_DCreative.objects.all()
    serializer_class = S_directory_DCreativeSerializers


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CalculaterViewSet(viewsets.ModelViewSet):
    queryset = Calculater.objects.all()
    serializer_class = CalculaterSerializer


    def create(self, request, *args, **kwargs):
        if Calculater.objects.filter(
                creative=request.data['creative']
        ).exists():
            raise ValidationError(
                "Формат размещения уже выбран")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calculater = serializer.save()
        creative = calculater.creative
        creative_data = [creative.name, creative.link, creative.price]
        response_data = serializer.data
        response_data['creative'] = creative_data
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        calculater = serializer.save()
        creative_data = [calculater.creative.name,
                         calculater.creative.link,
                         calculater.creative.price]
        response_data = serializer.data
        response_data['creative'] = creative_data
        return Response(response_data)

    def perform_destroy(self, instance):
        instance.creative.in_calculater = False
        instance.creative.save()
        instance.delete()


class AuditoriesViewSet(viewsets.ModelViewSet):
    queryset = Auditories.objects.all()
    serializer_class = AuditoriesSerializers

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChangeAuditoriesViewSet(viewsets.ModelViewSet):
    queryset = ChangeAuditories.objects.all()
    serializer_class = ChangeAuditoriesSerializers

    def create(self, request, *args, **kwargs):
        if ChangeAuditories.objects.filter(
                auditories=request.data['auditories']
        ).exists():
            raise ValidationError(
                "Специальность уже выбрана")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        changeauditories = serializer.save()
        auditories = changeauditories.auditories
        auditories_data = [auditories.speciality, auditories.count_doc]
        response_data = serializer.data
        response_data['auditories'] = auditories_data
        return Response(response_data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.auditories.in_changeauditories = False
        instance.auditories.save()
        instance.delete()


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializers

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset,
                                         many=True)
        return Response(serializer.data)


class AccommodationViewSet(viewsets.ModelViewSet):
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializers

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        accommodation = serializer.save()
        service = accommodation.service
        service_data = [service.title,
                           service.link]
        response_data = serializer.data
        response_data['service'] = service_data
        return Response(response_data,
                        status=status.HTTP_201_CREATED)
