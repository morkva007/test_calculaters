from rest_framework import serializers
from decimal import Decimal, DivisionByZero
from .models import (
    Calculater,
    S_directory_DCreative,
    Auditories,
    ChangeAuditories,
    Service,
    Accommodation
)
from django.db.models import Sum, IntegerField, Value
from django.db.models.functions import Coalesce, Cast


class S_directory_DCreativeSerializers(serializers.ModelSerializer):

    class Meta:
        model = S_directory_DCreative
        fields = ('name', 'link', 'price', 'in_calculater')


class CalculaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calculater
        fields = '__all__'

    def create(self, validated_data):
        creative = validated_data.get('creative')
        count_r = validated_data.get('count_r')
        price_without_NDS = creative.price * count_r
        NDS = price_without_NDS * Decimal('0.2')
        price_with_NDS = price_without_NDS + NDS
        validated_data['price_without_NDS'] = price_without_NDS
        validated_data['NDS'] = NDS
        validated_data['price_with_NDS'] = price_with_NDS
        # создаем запись в модели Calculater
        calculater = super().create(validated_data)
        # получаем связанную запись в модели S_directory_DCreative
        dcreative = calculater.creative
        # изменяем значение поля in_calculater на True
        dcreative.in_calculater = True
        dcreative.save()
        return calculater

    def update(self, calculater, validated_data):
        creative = validated_data.pop('creative')
        count_r = validated_data.pop('count_r')

        for key, value in validated_data.items():
            setattr(calculater, key, value)

        if creative:
            old_creative = calculater.creative
            calculater.creative = creative
            price_without_NDS = creative.price * count_r
            NDS = price_without_NDS * Decimal('0.2')
            price_with_NDS = price_without_NDS + NDS
            calculater.price_without_NDS = price_without_NDS
            calculater.NDS = NDS
            calculater.price_with_NDS = price_with_NDS

            old_creative.in_calculater = False
            old_creative.save()

            creative.in_calculater = True
            creative.save()

        if count_r:
            calculater.count_r = count_r
            price_without_NDS = calculater.creative.price * count_r
            NDS = price_without_NDS * Decimal('0.2')
            price_with_NDS = price_without_NDS + NDS
            calculater.price_without_NDS = price_without_NDS
            calculater.NDS = NDS
            calculater.price_with_NDS = price_with_NDS

        calculater.save()

        return calculater

    #  переопредеяем метод для того, чтобы в выводе
    #  querset в ключе 'creative' отражался список с
    #  именем, ценой и ссылкой
    def to_representation(self, instance):
        rep = super(CalculaterSerializer,
                    self).to_representation(instance)
        rep[
            'creative'] = [
            instance.creative.name,
            instance.creative.link,
            instance.creative.price
        ]
        return rep


class AuditoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = Auditories
        fields = (
        'speciality',
        'count_doc',
        'coefficient',
        'count_doc_GRP',
        'in_changeauditories'
        )


class ChangeAuditoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = ChangeAuditories
        fields = '__all__'

    def create(self, validated_data):
        changeauditories = super().create(validated_data)
        ch_auditories = changeauditories.auditories
        ch_auditories.in_changeauditories = True
        ch_auditories.save()
        return changeauditories

    def delete(self, instance):
        instance.auditories.in_changeauditories = False
        instance.auditories.save()
        instance.delete()

    def to_representation(self, instance):
        rep = super(ChangeAuditoriesSerializers,
                    self).to_representation(instance)
        rep[
            'auditories'] = [
            instance.auditories.speciality,
            instance.auditories.count_doc
        ]
        return rep

class ServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'




class AccommodationSerializers(serializers.ModelSerializer):
    # при использовании поля выбора в сериализаторе
    # нужно обязательно использовать ChoiceField иначе
    # будет возникать ошибка, что поле не может быть
    # пустым даже если в модеи указать null=True,
    # blank=True. Если необходимо указать поле с
    # удобочитаемом формате с использованием
    # source='get_FOO_display', то в сериализаторе
    # оно указывается отдельно
    season = serializers.ChoiceField(choices=Accommodation.SEASON)
    season_display_value = serializers.CharField(
        source='get_season_display', read_only=True
    )

    class Meta:
        model = Accommodation
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.specialyties:
            data[
                'specialyties'] = instance.specialyties.auditories.speciality
        else:
            querset = ChangeAuditories.objects.filter(
                auditories__isnull=False)
            auditories_list = querset.values_list(
                'auditories__speciality', flat=True)
            data['specialyties'] = ', '.join(
                auditories_list)
        data['service'] = [
            instance.service.title,
            instance.service.link
        ]
        return data

    def create(self, validated_data):
        season = validated_data.get('season')
        service = validated_data.get('service')
        specialyties = validated_data.get('specialyties')
        count_a = validated_data.get('count_a')
        discount = validated_data.get('discount')
        season_coeff = None
        if season == 'L':
            season_coeff = Decimal('-0.25')
        elif season == 'N':
            season_coeff = Decimal('-0.00')
        elif season == 'H':
            season_coeff = Decimal('0.25')
        season_coeff = season_coeff
        if specialyties is None:
            doc_count = ChangeAuditories.objects.filter(
            auditories__isnull=False).aggregate(
                total=Sum('auditories__count_doc')
            )['total'] or 0
            count_doc = doc_count
        else:
            if specialyties:
                count_doc = int(
                    specialyties.auditories.count_doc)
            else:
                count_doc = 0
        if specialyties and service.group == 1:
            if count_doc < 10000:
                price = service.price_before_10000 * count_doc
            elif 10001 < count_doc < 25000:
                price = service.price_before_25000 * count_doc
            else:
                price = service.price_after_25000 * count_doc
        if specialyties and service.group == 2:
            if count_doc < 10000:
                price = (
                                     service.price_before_10000 * specialyties.auditories.coefficient
                             ) * count_doc / doc_count * count_a
            elif 10001 < count_doc < 25000:
                price = (
                                        service.price_before_25000 * specialyties.auditories.coefficient
                                         ) * count_doc / doc_count * count_a
            else:
                price = (
                                         service.price_after_25000 * specialyties.auditories.coefficient
                                         ) * count_doc / doc_count * count_a
        if specialyties and service.group == 3:
            if count_doc < 10000:
                price = service.price_before_10000
            elif 10001 < count_doc < 25000:
                price = service.price_before_25000
            else:
                price = service.price_after_25000
        if specialyties and service.group == 4:
            price = service.price_before_10000
        if specialyties is None:
            queryset = ChangeAuditories.objects.filter(
                auditories__isnull=False)
            price_one = 0
            price_sum = 0

            for obj in queryset:
                if obj.auditories:
                    count_doc = int(obj.auditories.count_doc)
                    if service.group == 1:
                        if count_doc < 10000:
                            price_old  = service.price_before_10000 * count_doc * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        elif 10001 < count_doc < 25000:
                            price_old  = service.price_before_25000 * count_doc * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        else:
                            price_old  = service.price_after_25000 * count_doc * Decimal(
                                obj.auditories.coefficient)
                        price_one += price_old
                    elif service.group == 2:
                        if count_doc < 10000:
                            price_old  = (
                                            service.price_before_10000 * Decimal(obj.auditories.coefficient)
                                         ) * count_doc / doc_count * count_a
                        elif 10001 < count_doc < 25000:
                            price_old  = (
                                            service.price_before_25000 * Decimal(obj.auditories.coefficient)
                                         ) * count_doc / doc_count * count_a
                        else:
                            price_old  = (
                                            service.price_after_25000 * Decimal(
                                             obj.auditories.coefficient)) * count_doc / doc_count * count_a
                    elif service.group == 3:
                        if count_doc < 10000:
                            price_old  = service.price_before_10000
                        elif 10001 < count_doc < 25000:
                            price_old  = service.price_before_25000
                        else:
                            price_old  = service.price_after_25000
                    elif service.group == 4:
                        price_old = service.price_before_10000 * Decimal(obj.auditories.coefficient)
                        price_one += price_old
                    price_sum += price_old
            if service.group == 2:
                price = price_sum / count_a
            elif service.group == 3:
                price = price_sum
            else:
                price = price_one

        if season_coeff is not None and count_a is not None:
            price_not_NDS = (Decimal(str(price)) + Decimal(
                str(price)) * Decimal(
                str(season_coeff))) * Decimal(
                str(count_a))
        else:
            price_not_NDS = Decimal('0.00')
        discount_rub = discount * price_not_NDS
        price_d = price_not_NDS - discount_rub
        final_price = price_d * Decimal(
            '1.20')
        NDS = final_price - price_d
        unit = service.unit
        if service.group == 2:
            kpi = count_a
        else:
            kpi = count_a * int(
                    count_doc / Decimal('1000') * service.kpi_sd)
        try:
            cost = int(price_d / kpi)
        except DivisionByZero:
            cost = Decimal('0.00')
        fte = kpi * service.fte
        total_grp = ChangeAuditories.objects.filter(
            auditories__isnull=False).aggregate(
            total_grp=Sum(
                'auditories__count_doc_GRP')
        )['total_grp'] or 0
        if total_grp == 0:
            grp = Decimal('0.00')
        else:
            if service.title == 'Баннер (Сквозной в ленте сайта)':
                try:
                    grp = (kpi / Decimal('6')) / total_grp
                except TypeError:
                    grp = Decimal('0.00')

            elif (service.title == 'Лидерборд' or
                  service.title == 'Брендированная подложка' or
                  service.title == 'Текстово-рекламный блок'):
                try:
                    grp = (kpi / Decimal('5')) / total_grp
                except TypeError:
                    grp = Decimal('0.00')
            elif service.title == 'Inread-видео':
                try:
                    grp = (kpi / Decimal('3')) / total_grp
                except TypeError:
                    grp = Decimal('0.00')
            elif service.title == 'Фулскрин (Полноэкранный баннер на 18 сек)':
                try:
                    grp = (kpi / Decimal('2')) / total_grp
                except TypeError:
                    grp = Decimal('0.00')
            else:
                try:
                    grp = (kpi / Decimal('1.00')) / total_grp
                except TypeError:
                    grp = Decimal('0.00')
        validated_data['season'] = season
        validated_data['season_coeff'] = season_coeff
        validated_data['count_doc'] = count_doc
        validated_data['discount_rub'] = discount_rub
        validated_data['price'] = price
        validated_data['price_d']  = price_d
        validated_data['price_not_NDS'] = price_not_NDS
        validated_data['unit'] = unit
        validated_data['NDS'] = NDS
        validated_data['final_price'] = final_price
        validated_data['cost'] = cost
        validated_data['fte'] = fte
        validated_data['kpi'] = kpi
        validated_data['grp'] = grp
        accommodation = super().create(validated_data)
        return accommodation
