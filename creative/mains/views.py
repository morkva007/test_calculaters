from rest_framework import viewsets, status
from datetime import datetime as dt
from django.http import HttpResponse
from creative.settings import DATE_TIME_FORMAT
import csv
from rest_framework.response import Response
from .models import (
    Calculater,
    S_directory_DCreative,
    Auditories,
    ChangeAuditories,
    Service,
    Accommodation,
    ResultTable
)
from rest_framework.validators import ValidationError
from .serializers import (
    CalculaterSerializer,
    S_directory_DCreativeSerializers,
    AuditoriesSerializers,
    ChangeAuditoriesSerializers,
    ServiceSerializers,
    AccommodationSerializers,
    ResultTableSerializers)
from rest_framework.decorators import action
from django.db.models import F

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

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get(
            'name')
        if name:
            queryset = queryset.filter(
                    name=name)
        return queryset


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

    # доступно по ссылке http://127.0.0.1:8000/mains/changea/?name={name}
    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get(
            'name')
        if name:
            queryset = queryset.filter(
                    name=name)
        return queryset

    @action(detail=False, methods=['post'])
    def create_changea(self, name=None, pk=None):
        if ChangeAuditories.objects.filter(
                    name=name, pk=pk
            ).exists():
            raise ValidationError(
                    'Специальность уже выбрана')
        changea = ChangeAuditories.objects.create(
                name=name, pk=pk)
        serializer = ChangeAuditories(changea)
        auditories = changea.auditories
        auditories_data = [auditories.speciality,
                               auditories.count_doc]
        response_data = serializer.data
        response_data[
                'auditories'] = auditories_data
        return Response(response_data,
                            status=status.HTTP_201_CREATED)

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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        accommodation = serializer.save()
        service_data = [accommodation.service.title,
                         accommodation.service.link]
        response_data = serializer.data
        response_data['service'] = service_data
        return Response(response_data)

    def perform_destroy(self, instance):
        instance.specialyties.auditories.in_accommodation = False
        instance.specialyties.auditories.save()
        instance.delete()

    # доступно по ссылке http://127.0.0.1:8000/mains/accommodation/?name={name}
    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get(
            'name')
        if name:
            queryset = queryset.filter(
                    name=name)
        return queryset


class ResultTableViewSet(viewsets.ModelViewSet):
    queryset = ResultTable.objects.all()
    serializer_class = ResultTableSerializers

    # http://127.0.0.1:8000/mains/resulttable/download_result_table/?name=<selected_name>
    @action(methods=('get',), detail=False)
    def download_result_table(self, request):
        result_table = ResultTable.objects.filter(
            name=request.GET.get('name'))
        accommodation = result_table.first().name_accommodation
        calculater = result_table.first().name_calculater
        filename = f'{result_table.first().name}_resulttable.csv'
        result = [
            f'Итоговая таблица для калькуляторов:\n'
            f'"Формат размещения" № {accommodation}\n'
            f'"D-Creative" № {calculater}\n\n'
            f'{dt.now().strftime(DATE_TIME_FORMAT)}\n'
        ]
        result_1 = [f'\n\nКалькулятор Формат размещения № {accommodation}\n\n']
        result_2 = [f'\n\nКалькулятор "D-Creative" № {calculater}\n\n']
        response = HttpResponse(
            content_type='text/csv; charset=utf-8')
        response.write('\ufeff'.encode('utf-8')) # добавляем BOM
        writer = csv.writer(response, delimiter=';', lineterminator='\r\n')
        response.write(str.encode(''.join(
            result)))
        writer.writerow(['{:<10}'.format('Специальность_врача'),
                         '{:<10}'.format('Количество врачей'),
                         '{:<10}'.format('Цена без НДС для Формата размещения'),
                         '{:<10}'.format('Цена с НДС для Формата размещения'),
                         '{:<10}'.format('Цена без НДС для D-Creative'),
                         '{:<10}'.format('Цена с НДС для D-Creative')])
        for r in result_table.values('result_list'):
            for i in r['result_list']:
                writer.writerow(['{:<10}'.format(i['doctor']['speciality']),
                                 '{:<10}'.format(i['doctor']['count_doc']),
                                 '{:<10}'.format(i['accommodation_price_not_NDS']),
                                 '{:<10}'.format(i[
                                     'accommodation_price_with_NDS']),
                                 '{:<10}'.format(i[
                                     'calculator_price_not_NDS']),
                                 '{:<10}'.format(i[
                                     'calculator_price_with_NDS'])
                                 ])
        response.write(str.encode(''.join(
            result_2)))
        writer.writerow(['{:<10}'.format('Формат размещения'),
                         '{:<10}'.format('Количество'),
                         '{:<10}'.format('Цена без НДС'),
                         '{:<10}'.format('Цена с НДС'),
                         '{:<10}'.format('НДС')])
        calculater_obj = Calculater.objects.filter(name=calculater).values()
        for i in calculater_obj:
            f = i['creative_id']
            writer.writerow(['{:<10}'.format(
                S_directory_DCreative.objects.get(id=f).name),
                             '{:<10}'.format(
                                 i['count_r']),
                             '{:<10}'.format(i[
                                                 'price_without_NDS']),
                             '{:<10}'.format(i[
                                                 'NDS']),
                             '{:<10}'.format(i[
                                                 'price_with_NDS'])
                             ])
        response.write(str.encode(''.join(
            result_1)))
        writer.writerow(
            ['{:<10}'.format('Формат размещения'),
             '{:<10}'.format('Специальность'),
             '{:<10}'.format('Количество врачей'),
             '{:<10}'.format('Сезон'),
             '{:<10}'.format('Сезонный коэффициент'),
             '{:<10}'.format('Цена за единицу'),
             '{:<10}'.format('Количество'),
             '{:<10}'.format('Скидка'),
             '{:<10}'.format('Скидка в рублях'),
             '{:<10}'.format('Цена без НДС'),
             '{:<10}'.format('Цена с учетом скидки'),
             '{:<10}'.format('НДС'),
             '{:<10}'.format('Цена с НДС'),
             '{:<10}'.format('Еиница измерения'),
             '{:<10}'.format('kpi'),
             '{:<10}'.format('Стоимость за единицу'),
             '{:<10}'.format('fte'),
             '{:<10}'.format('grp')
             ])
        accommodation_obj = Accommodation.objects.filter(name=accommodation).values()
        for i in accommodation_obj:
            f = i['service_id']
            s = i['specialyties_id']
            x = Accommodation.objects.get(id=i['id'])
            season_display_value = x.get_season_display()
            if s is None:
                s = "Все из списка"
            else:
                try:
                    s = ChangeAuditories.objects.get(
                        id=s).auditories
                except ChangeAuditories.DoesNotExist:
                    s = "None"
            writer.writerow(['{:<10}'.format(
                Service.objects.get(
                    id=f).title),
                '{:<10}'.format(str(s)),
                '{:<10}'.format(
                    i['count_doc']),
                '{:<10}'.format(
                    season_display_value),
                '{:<10}'.format(
                    i['season_coeff']),
                '{:<10}'.format(
                    i['price']),
                '{:<10}'.format(
                    i['count_a']),
                '{:<10}'.format(
                    i['discount']),
                '{:<10}'.format(
                    i['discount_rub']),
                '{:<10}'.format(
                    i['price_not_NDS']),
                '{:<10}'.format(
                    i['price_d']),
                '{:<10}'.format(
                    i['NDS']),
                '{:<10}'.format(
                    i['final_price']),
                '{:<10}'.format(
                    i['unit']),
                '{:<10}'.format(
                    i['kpi']),
                '{:<10}'.format(
                    i['cost']),
                '{:<10}'.format(
                    i['fte']),
                '{:<10}'.format(
                    i['grp'])
                ])
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
