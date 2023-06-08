from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.core.validators import MinValueValidator
from decimal import Decimal, DivisionByZero

User = get_user_model()


#  Калькулятор D-creative справочник
class S_directory_DCreative(models.Model):
    name = models.CharField(max_length=150)
    link = models.URLField(verbose_name='Ссылка', max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    in_calculater = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} {self.link} {self.price}'


class Calculater(models.Model):
    name = models.CharField(max_length=250)
    # null=True необходимо устанавливать по умолчанию
    # для строк, которые могут быть не заполнены
    creative = models.ForeignKey(
        S_directory_DCreative,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Формат размещения'
    )
    count_r = models.IntegerField()
    # max_digits указываются все цифры в числе в том
    # числе, которые были после запятой.
    # для типа поля models.DecimalField в случае
    # установки по умолчанию null=True
    # нужно установить дополнительный парметр  валидации
    # validators=[MinValueValidator(Decimal('0.00'))]
    # для типа поля models.IntegerField() достаточно
    # просто указать null=True
    price_without_NDS=models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена без НДС'
    )
    NDS=models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='НДС')
    price_with_NDS=models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена с НДС'
    )

    def save(self, *args, **kwargs):
        self.price_without_NDS = (
                self.creative.price * self.count_r
        )
        self.NDS = (
                self.price_with_NDS -
                self.price_without_NDS
        )
        self.price_with_NDS = (
                self.price_without_NDS * Decimal('1.2')
        )
        super().save(*args, **kwargs)


class Auditories(models.Model):
    id = models.IntegerField(primary_key=True)
    speciality = models.CharField(
        max_length=150,
        verbose_name='Специализация'
    )
    count_doc = models.CharField(
        max_length=7,
        verbose_name='Количество докторов'
    )
    coefficient = models.CharField(
        max_length=4,
        verbose_name='Коэффициент специализации'
    )
    count_doc_GRP = models.CharField(
        max_length=7,
        verbose_name='Коэффициент GRP'
    )
    in_changeauditories = models.BooleanField(
        default=False
    )
    in_accommodation = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['speciality']

    def __str__(self):
        return self.speciality


class ChangeAuditories(models.Model):
    name = models.CharField(max_length=150,
                            null=True,
                            blank=True)
    auditories = models.ForeignKey(
        Auditories,
        on_delete=models.CASCADE,
        verbose_name='Выбранная аудитория',
        related_name='change_auditories')

    def __str__(self):
        return self.auditories.speciality


class Service(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=150)
    price_before_10000 = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    price_before_25000 = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    price_after_25000 = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    kpi_sd = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    unit = models.CharField(max_length=150, blank=True)
    group = models.IntegerField()
    fte = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    link = models.URLField(max_length=200, blank=True)

    class Meta:
        ordering = ['title']


class Accommodation(models.Model):
    SEASON=[
        ('L', 'Низкий'),
        ('N', 'Без сезона'),
        ('H', 'Высокий сезон')
    ]

    name = models.CharField(max_length=100, null=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Формат размещения')
    specialyties = models.ForeignKey(
        ChangeAuditories,
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        default=None,
        verbose_name='Специализация врача'
    )
    name_change = models.CharField(max_length=150)
    count_doc = models.IntegerField(null=True, blank=True)
    season = models.CharField(
        max_length=13,
        choices=SEASON,
        verbose_name='Выбор сезона')
    season_coeff = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Коэффициент сезонности'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена за единицу'
    )
    count_a = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00,
        verbose_name='Количество'
    )

    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    discount_rub = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Скидка в рублях'
    )
    price_not_NDS = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена без НДС'
    )
    price_d = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена с учетом скидки'
    )
    NDS = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))],
        verbose_name='НДС'
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена с НДС'
    )
    unit = models.CharField(max_length=100, null=True, blank=True)
    kpi = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))]
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))],
        verbose_name='Стоимость за единицу'
    )
    fte = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))]
    )
    grp = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00'))]
    )

    def save(self, *args, **kwargs):
        # name_change = self.specialyties.name
        if self.specialyties is None:
            doc_count = ChangeAuditories.objects.filter(
                name=self.name_change,
                auditories__isnull=False).aggregate(
                total=Sum('auditories__count_doc')
            )['total'] or 0
            self.count_doc = doc_count
        else:
            if self.specialyties:
                self.count_doc = int(
                    self.specialyties.auditories.count_doc)
            else:
                self.count_doc = 0
        season_coeff = None
        if self.season == 'L':
            season_coeff = Decimal('-0.25')
        elif self.season == 'N':
            season_coeff = Decimal('-0.00')
        elif self.season == 'H':
            season_coeff = Decimal('0.25')
        self.season_coeff = season_coeff
        if self.specialyties and self.service.group == 1:
            if self.count_doc < 10000:
                self.price = self.service.price_before_10000 * self.count_doc
            elif 10001 < self.count_doc < 25000:
                self.price = self.service.price_before_25000 * self.count_doc
            else:
                self.price = self.service.price_after_25000 * self.count_doc
        if self.specialyties and self.service.group == 2:
            if self.count_doc < 10000:
                self.price = (
                                     self.service.price_before_10000 * self.specialyties.auditories.coefficient
                             ) * self.count_doc / doc_count * self.count_a
            elif 10001 < self.count_doc < 25000:
                self.price = (self.service.price_before_25000 * self.specialyties.auditories.coefficient
                             ) * self.count_doc / doc_count * self.count_a
            else:
                self.price = (self.service.price_after_25000 * self.specialyties.auditories.coefficient
                             ) * self.count_doc / doc_count * self.count_a
        if self.specialyties and self.service.group == 3:
            if self.count_doc < 10000:
                self.price = self.service.price_before_10000
            elif 10001 < self.count_doc < 25000:
                self.price = self.service.price_before_25000
            else:
                self.price = self.service.price_after_25000
        if self.specialyties and self.service.group == 4:
            self.price = self.service.price_before_10000
        if self.specialyties is None:
            queryset = ChangeAuditories.objects.filter(
                name=self.name_change,
                auditories__isnull=False)
            price_one = 0
            price_sum = 0
            for obj in queryset:
                if obj.auditories:
                    count_doc = int(obj.auditories.count_doc)
                    if self.service.group == 1:
                        if count_doc < 10000:
                            price = self.service.price_before_10000 * count_doc * Decimal(
                                obj.auditories.coefficient
                            )
                        elif 10001 < count_doc < 25000:
                            price = self.service.price_before_25000 * count_doc * Decimal(
                                obj.auditories.coefficient)
                        else:
                            price = self.service.price_after_25000 * count_doc * Decimal(
                                obj.auditories.coefficient)
                        price_one += price
                    elif self.service.group == 2:
                        if count_doc < 10000:
                            price = (
                                                self.service.price_before_10000 * Decimal(obj.auditories.coefficient)
                                    ) * count_doc / doc_count * self.count_a
                        elif 10001 < count_doc < 25000:
                            price = (
                                                self.service.price_before_25000 * Decimal(obj.auditories.coefficient
                                                                                          )
                                    ) * count_doc / doc_count * self.count_a
                        else:
                            price = (
                                                self.service.price_after_25000 * Decimal(obj.auditories.coefficient)
                                    ) * count_doc / doc_count * self.count_a
                    elif self.service.group == 3:
                        if count_doc < 10000:
                            price = self.service.price_before_10000
                        elif 10001 < count_doc < 25000:
                            price = self.service.price_before_25000
                        else:
                            price = self.service.price_after_25000
                    elif self.service.group == 4:
                        price = self.service.price_before_10000 * Decimal(obj.auditories.coefficient)
                        price_one += price
                    price_sum += price
            if self.service.group == 2:
                self.price = price_sum / self.count_a
            elif self.service.group == 3:
                self.price = price_sum
            else:
                self.price = price_one
        if self.season_coeff is not None and self.count_a is not None:
            self.price_not_NDS = (Decimal(str(self.price)) + Decimal(str(self.price)) * Decimal(str(self.season_coeff))) * Decimal(str(self.count_a))
        else:
            self.price_not_NDS = Decimal('0.00')
        self.discount_rub = self.discount * self.price_not_NDS
        self.price_d = self.price_not_NDS - self.discount_rub
        self.final_price = self.price_d * Decimal('1.20')
        self.NDS = self.final_price - self.price_d
        self.unit = self.service.unit
        if self.service.group == 2:
            self.kpi = self.count_a
        else:
            self.kpi = self.count_a * int(
                        self.count_doc / Decimal('1000') * self.service.kpi_sd)
        try:
            self.cost = int(self.price_d / self.kpi)
        except DivisionByZero:
            self.cost = Decimal('0.00')
        self.fte = self.kpi * self.service.fte
        total_grp = ChangeAuditories.objects.filter(
            name=self.name_change,
            auditories__isnull=False).aggregate(
            total_grp=Sum(
                'auditories__count_doc_GRP')
        )['total_grp'] or 0
        if total_grp == 0:
            self.grp = Decimal('0.00')
        else:
            if self.service.title == 'Баннер (Сквозной в ленте сайта)':
                try:
                    self.grp = (self.kpi / Decimal('6')) / total_grp
                except TypeError:
                    self.grp = Decimal('0.00')

            elif (self.service.title == 'Лидерборд' or
                  self.service.title == 'Брендированная подложка' or
                  self.service.title == 'Текстово-рекламный блок'):
                try:
                    self.grp = (self.kpi / Decimal('5')) / total_grp
                except TypeError:
                    self.grp = Decimal('0.00')
            elif self.service.title == 'Inread-видео':
                try:
                    self.grp = (self.kpi / Decimal('3')) / total_grp
                except TypeError:
                    self.grp = Decimal('0.00')
            elif self.service.title == 'Фулскрин (Полноэкранный баннер на 18 сек)':
                try:
                    self.grp = (self.kpi / Decimal('2')) / total_grp
                except TypeError:
                    self.grp = Decimal('0.00')
            else:
                try:
                    self.grp = (self.kpi / Decimal(
                        '1.00')) / total_grp
                except TypeError:
                    self.grp = Decimal('0.00')

        super().save(*args, **kwargs)


class ResultTable(models.Model):
    name = models.CharField(max_length=150)
    name_accommodation = models.CharField(max_length=150, blank=True, null=True)
    name_calculater = models.CharField(max_length=150, blank=True, null=True)
    name_change = models.CharField(max_length=150, blank=True, null=True)
    result_list = models.JSONField(default=list, blank=True, null=True)

    def save(self, *args, **kwargs):
        result_list = []
        # получаем уникальные значения специальностей
        change_a_list = Accommodation.objects.filter(
            name=self.name_accommodation, name_change=self.name_change
        ).values_list('specialyties', flat=True).distinct()
        change_a = []
        for i in change_a_list:
            if i is not None:
                select_auditories = ChangeAuditories.objects.get(id=i)
                if select_auditories not in change_a:
                    change_a.append(
                        select_auditories)
            else:
                select_auditories = ChangeAuditories.objects.filter(
                    name=self.name_change
                )
                for y in select_auditories:
                    if y not in change_a:
                        change_a.append(
                            y)
        for a in change_a:
            doctor = Auditories.objects.get(speciality=a)
            doctor_dict = {'speciality': doctor.speciality,
                           'count_doc': doctor.count_doc}

            share = Decimal(doctor_dict['count_doc']) / ChangeAuditories.objects.filter(
                    name=self.name_change, auditories__isnull=False
                ).aggregate(total=Sum('auditories__count_doc')
                            )['total']
            if Accommodation.objects.filter(
                    name=self.name_accommodation,
                    name_change=self.name_change,
                    specialyties=a).exists():
                price_not_NDS = Accommodation.objects.filter(
                    name=self.name_accommodation, name_change=self.name_change,
                    specialyties=a).aggregate(total=Sum(
                    'price_d'))['total']
                accommodation_price_not_NDS = (
                                                      Accommodation.objects.filter(
                                                          name=self.name_accommodation,
                                                          name_change=self.name_change,
                                                          specialyties=None
                                                      ).aggregate(total=Sum(
                                                          'price_d'))['total']
                                              ) * share + price_not_NDS
                accommodation_price_with_NDS = accommodation_price_not_NDS * Decimal('1.2')
            else:
                accommodation_price_not_NDS = Accommodation.objects.filter(
                    name=self.name_accommodation,
                    name_change=self.name_change,
                    specialyties=None
                                             ).aggregate(
                    total=Sum('price_d'))[
                    'total'] * share
                accommodation_price_with_NDS = accommodation_price_not_NDS * Decimal('1.2')

            calculator_price_not_NDS = Calculater.objects.filter(
                    name=self.name_calculater).aggregate(
                total=Sum('price_without_NDS')
            )['total'] / ChangeAuditories.objects.filter(
                name=self.name_change, auditories__isnull=False
            ).aggregate(total=Sum('auditories__count_doc')
                        )['total'] * Decimal(doctor_dict['count_doc'])
            calculator_price_with_NDS = Calculater.objects.filter(
                    name=self.name_calculater).aggregate(
                total=Sum('price_with_NDS')
            )['total'] / ChangeAuditories.objects.filter(
                name=self.name_change, auditories__isnull=False
            ).aggregate(total=Sum('auditories__count_doc')
                        )['total'] * Decimal(doctor_dict['count_doc'])
            result_list.append({
                'doctor': doctor_dict,
                'accommodation_price_not_NDS': round(float(accommodation_price_not_NDS), 2),
                'accommodation_price_with_NDS': round(float(accommodation_price_with_NDS), 2),
                'calculator_price_not_NDS': round(float(calculator_price_not_NDS), 2),
                'calculator_price_with_NDS': round(float(calculator_price_with_NDS), 2)
            })
        self.result_list = result_list
        super(ResultTable, self).save(*args, **kwargs)
