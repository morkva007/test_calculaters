from rest_framework import serializers
from decimal import Decimal, DivisionByZero
from .models import (
    Calculater,
    S_directory_DCreative,
    Auditories,
    ChangeAuditories,
    Service,
    Accommodation,
    ResultTable
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
        'in_changeauditories',
        'in_accommodation'
        )


class ChangeAuditoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = ChangeAuditories
        fields = '__all__'

    def validate(self, data):
        """
        Проверка на уникальность записи
        """
        name = data.get('name')
        auditories = data.get('auditories')
        if ChangeAuditories.objects.filter(name=name,
                                           auditories=auditories).exists():
            raise serializers.ValidationError(
                'Специальность уже выбрана')
        return data

    def create(self, validated_data):
        changeauditories = super().create(validated_data)
        ch_auditories = changeauditories.auditories
        ch_auditories.in_changeauditories = True
        ch_auditories.save()
        return changeauditories

    def delete(self, instance):
        if instance.auditories.count() == 1:
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
        source='get_season_display', read_only=True)


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
                name=instance.name_change,
                auditories__isnull=False)
            auditories_list = querset.values_list(
                'auditories__speciality', flat=True)
            data['specialyties'] = ', '.join(
                auditories_list)
        if 'service' not in data:
            data['service'] = [
                instance.service.title,
                instance.service.link
            ]
        else:
            del data['service']
        return data

    def create(self, validated_data):
        season = validated_data.get('season')
        service = validated_data.get('service')
        specialyties = validated_data.get('specialyties')
        name_change = validated_data.get('name_change')
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
                name=name_change,
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
            if specialyties:
                speciality = specialyties.auditories
                speciality.in_accommodation = True
                speciality.save()
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
                name=name_change,
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
            name=name_change,
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
        validated_data['name_change'] = name_change
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

    def update(self, accommodation, validated_data):
        service = validated_data.pop('service')
        count_a = validated_data.pop('count_a')
        if 'specialyties' in validated_data:
            specialyties = validated_data.pop(
                'specialyties')
        else:
            specialyties = None
        season = validated_data.pop('season')
        discount = validated_data.pop('discount')

        for key, value in validated_data.items():
            setattr(accommodation, key, value)
        if season:
            accommodation.season = season
            if season:
                season_coeff = None
                if season == 'L':
                    season_coeff = Decimal('-0.25')
                elif season == 'N':
                    season_coeff = Decimal('-0.00')
                elif season == 'H':
                    season_coeff = Decimal('0.25')
                season_coeff = season_coeff

                if specialyties is None:
                    doc_count = \
                        ChangeAuditories.objects.filter(
                            name=accommodation.name_change,
                            auditories__isnull=False).aggregate(
                            total=Sum(
                                'auditories__count_doc')
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
                        name=accommodation.name_change,
                        auditories__isnull=False)
                    price_one = 0
                    price_sum = 0

                    for obj in queryset:
                        if obj.auditories:
                            count_doc = int(
                                obj.auditories.count_doc)
                            if service.group == 1:
                                if count_doc < 10000:
                                    price_old = service.price_before_10000 * count_doc * Decimal(
                                        obj.auditories.coefficient)
                                    price_one += price_old
                                elif 10001 < count_doc < 25000:
                                    price_old = service.price_before_25000 * count_doc * Decimal(
                                        obj.auditories.coefficient)
                                    price_one += price_old
                                else:
                                    price_old = service.price_after_25000 * count_doc * Decimal(
                                        obj.auditories.coefficient)
                                price_one += price_old
                            elif service.group == 2:
                                if count_doc < 10000:
                                    price_old = (
                                                        service.price_before_10000 * Decimal(
                                                    obj.auditories.coefficient)
                                                ) * count_doc / doc_count * count_a
                                elif 10001 < count_doc < 25000:
                                    price_old = (
                                                        service.price_before_25000 * Decimal(
                                                    obj.auditories.coefficient)
                                                ) * count_doc / doc_count * count_a
                                else:
                                    price_old = (
                                                        service.price_after_25000 * Decimal(
                                                    obj.auditories.coefficient)) * count_doc / doc_count * count_a
                            elif service.group == 3:
                                if count_doc < 10000:
                                    price_old = service.price_before_10000
                                elif 10001 < count_doc < 25000:
                                    price_old = service.price_before_25000
                                else:
                                    price_old = service.price_after_25000
                            elif service.group == 4:
                                price_old = service.price_before_10000 * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            price_sum += price_old
                    if service.group == 2:
                        price = price_sum / count_a
                    elif service.group == 3:
                        price = price_sum
                    else:
                        price = price_one

                if season_coeff is not None and count_a is not None:
                    price_not_NDS = (Decimal(
                        str(price)) + Decimal(
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
        if count_a:
            accommodation.count_a = count_a
            season_coeff = None
            if season == 'L':
                season_coeff = Decimal('-0.25')
            elif season == 'N':
                season_coeff = Decimal('-0.00')
            elif season == 'H':
                season_coeff = Decimal('0.25')
            season_coeff = season_coeff

            if specialyties is None:
                doc_count = \
                    ChangeAuditories.objects.filter(
                        name=accommodation.name_change,
                        auditories__isnull=False).aggregate(
                        total=Sum(
                            'auditories__count_doc')
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
                    name=accommodation.name_change,
                    auditories__isnull=False)
                price_one = 0
                price_sum = 0

                for obj in queryset:
                    if obj.auditories:
                        count_doc = int(
                            obj.auditories.count_doc)
                        if service.group == 1:
                            if count_doc < 10000:
                                price_old = service.price_before_10000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            else:
                                price_old = service.price_after_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                            price_one += price_old
                        elif service.group == 2:
                            if count_doc < 10000:
                                price_old = (
                                                    service.price_before_10000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            elif 10001 < count_doc < 25000:
                                price_old = (
                                                    service.price_before_25000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            else:
                                price_old = (
                                                    service.price_after_25000 * Decimal(
                                                obj.auditories.coefficient)) * count_doc / doc_count * count_a
                        elif service.group == 3:
                            if count_doc < 10000:
                                price_old = service.price_before_10000
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000
                            else:
                                price_old = service.price_after_25000
                        elif service.group == 4:
                            price_old = service.price_before_10000 * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        price_sum += price_old
                if service.group == 2:
                    price = price_sum / count_a
                elif service.group == 3:
                    price = price_sum
                else:
                    price = price_one

            if season_coeff is not None and count_a is not None:
                price_not_NDS = (Decimal(
                    str(price)) + Decimal(
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
            if service.group == 2:
                kpi = count_a
            else:
                kpi = count_a * int(
                    count_doc / Decimal(
                        '1000') * service.kpi_sd)
        if discount:
            accommodation.discount = discount
            accommodation.count_a = count_a
            season_coeff = None
            if season == 'L':
                season_coeff = Decimal('-0.25')
            elif season == 'N':
                season_coeff = Decimal('-0.00')
            elif season == 'H':
                season_coeff = Decimal('0.25')
            season_coeff = season_coeff

            if specialyties is None:
                doc_count = \
                    ChangeAuditories.objects.filter(
                        name=accommodation.name_change,
                        auditories__isnull=False).aggregate(
                        total=Sum(
                            'auditories__count_doc')
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
                    name=accommodation.name_change,
                    auditories__isnull=False)
                price_one = 0
                price_sum = 0

                for obj in queryset:
                    if obj.auditories:
                        count_doc = int(
                            obj.auditories.count_doc)
                        if service.group == 1:
                            if count_doc < 10000:
                                price_old = service.price_before_10000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            else:
                                price_old = service.price_after_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                            price_one += price_old
                        elif service.group == 2:
                            if count_doc < 10000:
                                price_old = (
                                                    service.price_before_10000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            elif 10001 < count_doc < 25000:
                                price_old = (
                                                    service.price_before_25000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            else:
                                price_old = (
                                                    service.price_after_25000 * Decimal(
                                                obj.auditories.coefficient)) * count_doc / doc_count * count_a
                        elif service.group == 3:
                            if count_doc < 10000:
                                price_old = service.price_before_10000
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000
                            else:
                                price_old = service.price_after_25000
                        elif service.group == 4:
                            price_old = service.price_before_10000 * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        price_sum += price_old
                if service.group == 2:
                    price = price_sum / count_a
                elif service.group == 3:
                    price = price_sum
                else:
                    price = price_one

            if season_coeff is not None and count_a is not None:
                price_not_NDS = (Decimal(
                    str(price)) + Decimal(
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
        if service:
            accommodation.service = service
            season_coeff = None
            if season == 'L':
                season_coeff = Decimal('-0.25')
            elif season == 'N':
                season_coeff = Decimal('-0.00')
            elif season == 'H':
                season_coeff = Decimal('0.25')
            season_coeff = season_coeff
            if specialyties is None:
                doc_count = \
                ChangeAuditories.objects.filter(
                    name=accommodation.name_change,
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
                if specialyties:
                    speciality = specialyties.auditories
                    speciality.in_accommodation = True
                    speciality.save()
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
                    name=accommodation.name_change,
                    auditories__isnull=False)
                price_one = 0
                price_sum = 0

                for obj in queryset:
                    if obj.auditories:
                        count_doc = int(
                            obj.auditories.count_doc)
                        if service.group == 1:
                            if count_doc < 10000:
                                price_old = service.price_before_10000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            else:
                                price_old = service.price_after_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                            price_one += price_old
                        elif service.group == 2:
                            if count_doc < 10000:
                                price_old = (
                                                    service.price_before_10000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            elif 10001 < count_doc < 25000:
                                price_old = (
                                                    service.price_before_25000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            else:
                                price_old = (
                                                    service.price_after_25000 * Decimal(
                                                obj.auditories.coefficient)) * count_doc / doc_count * count_a
                        elif service.group == 3:
                            if count_doc < 10000:
                                price_old = service.price_before_10000
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000
                            else:
                                price_old = service.price_after_25000
                        elif service.group == 4:
                            price_old = service.price_before_10000 * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        price_sum += price_old
                if service.group == 2:
                    price = price_sum / count_a
                elif service.group == 3:
                    price = price_sum
                else:
                    price = price_one

            if season_coeff is not None and count_a is not None:
                price_not_NDS = (Decimal(
                    str(price)) + Decimal(
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
                    count_doc / Decimal(
                        '1000') * service.kpi_sd)
            try:
                cost = int(price_d / kpi)
            except DivisionByZero:
                cost = Decimal('0.00')
            fte = kpi * service.fte
            total_grp = \
            ChangeAuditories.objects.filter(
                name=accommodation.name_change,
                auditories__isnull=False).aggregate(
                total_grp=Sum(
                    'auditories__count_doc_GRP')
            )['total_grp'] or 0
            if total_grp == 0:
                grp = Decimal('0.00')
            else:
                if service.title == 'Баннер (Сквозной в ленте сайта)':
                    try:
                        grp = (kpi / Decimal(
                            '6')) / total_grp
                    except TypeError:
                        grp = Decimal('0.00')

                elif (service.title == 'Лидерборд' or
                      service.title == 'Брендированная подложка' or
                      service.title == 'Текстово-рекламный блок'):
                    try:
                        grp = (kpi / Decimal(
                            '5')) / total_grp
                    except TypeError:
                        grp = Decimal('0.00')
                elif service.title == 'Inread-видео':
                    try:
                        grp = (kpi / Decimal(
                            '3')) / total_grp
                    except TypeError:
                        grp = Decimal('0.00')
                elif service.title == 'Фулскрин (Полноэкранный баннер на 18 сек)':
                    try:
                        grp = (kpi / Decimal(
                            '2')) / total_grp
                    except TypeError:
                        grp = Decimal('0.00')
                else:
                    try:
                        grp = (kpi / Decimal(
                            '1.00')) / total_grp
                    except TypeError:
                        grp = Decimal('0.00')

        if specialyties:
            accommodation.specialyties = specialyties
            season_coeff = None
            if season == 'L':
                season_coeff = Decimal('-0.25')
            elif season == 'N':
                season_coeff = Decimal('-0.00')
            elif season == 'H':
                season_coeff = Decimal('0.25')
            season_coeff = season_coeff
            if specialyties is None:
                doc_count = \
                    ChangeAuditories.objects.filter(
                        name=accommodation.name_change,
                        auditories__isnull=False).aggregate(
                        total=Sum(
                            'auditories__count_doc')
                    )['total'] or 0
                count_doc = doc_count
            else:
                if specialyties:
                    count_doc = int(
                        specialyties.auditories.count_doc)
                else:
                    count_doc = 0
            if specialyties:
               old_speciality = accommodation.specialyties.auditories
               speciality = specialyties.auditories
               speciality.in_accommodation = True
               speciality.save()
               old_speciality.in_accommodation = False
               old_speciality.save()
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
                    name=accommodation.name_change,
                    auditories__isnull=False)
                price_one = 0
                price_sum = 0

                for obj in queryset:
                    if obj.auditories:
                        count_doc = int(
                            obj.auditories.count_doc)
                        if service.group == 1:
                            if count_doc < 10000:
                                price_old = service.price_before_10000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                                price_one += price_old
                            else:
                                price_old = service.price_after_25000 * count_doc * Decimal(
                                    obj.auditories.coefficient)
                            price_one += price_old
                        elif service.group == 2:
                            if count_doc < 10000:
                                price_old = (
                                                    service.price_before_10000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            elif 10001 < count_doc < 25000:
                                price_old = (
                                                    service.price_before_25000 * Decimal(
                                                obj.auditories.coefficient)
                                            ) * count_doc / doc_count * count_a
                            else:
                                price_old = (
                                                    service.price_after_25000 * Decimal(
                                                obj.auditories.coefficient)) * count_doc / doc_count * count_a
                        elif service.group == 3:
                            if count_doc < 10000:
                                price_old = service.price_before_10000
                            elif 10001 < count_doc < 25000:
                                price_old = service.price_before_25000
                            else:
                                price_old = service.price_after_25000
                        elif service.group == 4:
                            price_old = service.price_before_10000 * Decimal(
                                obj.auditories.coefficient)
                            price_one += price_old
                        price_sum += price_old
                if service.group == 2:
                    price = price_sum / count_a
                elif service.group == 3:
                    price = price_sum
                else:
                    price = price_one

            if season_coeff is not None and count_a is not None:
                price_not_NDS = (Decimal(
                    str(price)) + Decimal(
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
        accommodation.save()
        return accommodation


class ResultTableSerializers(serializers.ModelSerializer):
    class Meta:
        model = ResultTable
        fields = '__all__'

    def create(self, validated_data):
        name = validated_data.get('name')
        name_accommodation = validated_data.get('name_accommodation')
        name_calculater = validated_data.get('name_calculater')
        name_change = validated_data.get('name_change')
        result_list = []
        change_a_list = Accommodation.objects.filter(
            name=name_accommodation,
            name_change=name_change
        ).values_list('specialyties',
                      flat=True).distinct()
        change_a = []
        for i in change_a_list:
            if i is not None:
                select_auditories = ChangeAuditories.objects.get(
                    id=i)
                if select_auditories not in change_a:
                    change_a.append(
                        select_auditories)
            else:
                select_auditories = ChangeAuditories.objects.filter(
                    name=name_change
                )
                for y in select_auditories:
                    if y not in change_a:
                        change_a.append(
                            y)
        for a in change_a:
            doctor = Auditories.objects.get(
                speciality=a)
            # коичество врачей выводится в формате str
            doctor_dict = {
                'speciality': doctor.speciality,
                'count_doc': doctor.count_doc}
            share = Decimal(doctor_dict['count_doc']) / \
                    ChangeAuditories.objects.filter(
                        name=name_change,
                        auditories__isnull=False
                    ).aggregate(total=Sum(
                        'auditories__count_doc')
                                )['total']
            if Accommodation.objects.filter(
                    name=name_accommodation,
                    name_change=name_change,
                    specialyties=a).exists():
                price_not_NDS = \
                Accommodation.objects.filter(
                    name=name_accommodation,
                    name_change=name_change,
                    specialyties=a).aggregate(
                    total=Sum(
                        'price_d'))['total']

                accommodation_price_not_NDS = (
                                                      Accommodation.objects.filter(
                                                          name=name_accommodation,
                                                          name_change=name_change,
                                                          specialyties=None
                                                      ).aggregate(
                                                          total=Sum(
                                                              'price_d'))[
                                                          'total']
                                              ) * share + price_not_NDS
                accommodation_price_with_NDS = accommodation_price_not_NDS * Decimal('1.2')
            else:
                accommodation_price_not_NDS = \
                Accommodation.objects.filter(
                    name=name_accommodation,
                    name_change=name_change,
                    specialyties=None
                ).aggregate(
                    total=Sum('price_d'))[
                    'total'] * share
                accommodation_price_with_NDS = accommodation_price_not_NDS * Decimal('1.2')

            calculator_price_not_NDS = \
            Calculater.objects.filter(
                name=name_calculater).aggregate(
                total=Sum('price_without_NDS')
            )['total'] / \
            ChangeAuditories.objects.filter(
                name=name_change,
                auditories__isnull=False
            ).aggregate(
                total=Sum('auditories__count_doc')
                )['total'] * Decimal(doctor_dict['count_doc'])
            calculator_price_with_NDS = \
            Calculater.objects.filter(
                name=name_calculater).aggregate(
                total=Sum('price_with_NDS')
            )['total'] / \
            ChangeAuditories.objects.filter(
                name=name_change,
                auditories__isnull=False
            ).aggregate(
                total=Sum('auditories__count_doc')
                )['total'] * Decimal(doctor_dict['count_doc'])
            result_list.append({
                'doctor': doctor_dict,
                'accommodation_price_not_NDS': round(float(accommodation_price_not_NDS), 2),
                'accommodation_price_with_NDS': round(float(accommodation_price_with_NDS), 2),
                'calculator_price_not_NDS': round(float(calculator_price_not_NDS), 2),
                'calculator_price_with_NDS': round(float(calculator_price_with_NDS), 2)
            })
        validated_data['name'] = name
        validated_data['result_list'] = result_list
        resulttable = super().create(validated_data)
        return resulttable
