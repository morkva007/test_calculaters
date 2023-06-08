from django.contrib import admin
from .models import (Calculater,
                     S_directory_DCreative,
                     Auditories,
                     ChangeAuditories,
                     Service,
                     Accommodation,
                     ResultTable)
from decimal import Decimal


@admin.register(S_directory_DCreative)
class S_directory_DCreativeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'link',
        'price',
        'in_calculater'
    )
    list_filter = ('name',)
    search_fields = ['name']


@admin.register(Calculater)
class CalculaterAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'creative',
                    'count_r',
                    'price_without_NDS',
                    'NDS',
                    'price_with_NDS')
    list_filter = ('name',)
    search_fields = ('name__name',)
    autocomplete_fields = ('creative',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('creative')
        return queryset

    def link(self, obj):
        return obj.name.link
    link.short_description = 'Ссылка'

    def save_model(self, request, obj, form, change):
        if not obj.name or not obj.creative or not obj.count_r:
            raise ValueError('Заполните все обязательные поля')
        creative = obj.creative
        count_r = obj.count_r
        price_without_NDS = creative.price * count_r
        NDS = price_without_NDS * Decimal('0.2')
        price_with_NDS = price_without_NDS + NDS
        obj.price_without_NDS = price_without_NDS
        obj.NDS = NDS
        obj.price_with_NDS = price_with_NDS
        super().save_model(request, obj, form, change)
        dcreative = creative.s_directory_dcreative
        dcreative.in_calculater = True
        dcreative.save()


@admin.register(Auditories)
class AuditoriesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'speciality',
        'count_doc',
        'coefficient',
        'count_doc_GRP',
        'in_changeauditories',
        'in_accommodation'
    )
    search_fields = ('speciality',)


@admin.register(ChangeAuditories)
class ChangeAuditoriesAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'name',
                    'auditories',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'price_before_10000',
        'price_before_25000',
        'price_after_25000',
        'kpi_sd',
        'unit',
        'group',
        'fte',
        'link'
    )
    search_fields = ('name',)

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'service',
        'specialyties',
        'name_change',
        'count_doc',
        'season',
        'season_coeff',
        'price',
        'count_a',
        'discount',
        'discount_rub',
        'price_not_NDS',
        'price_d',
        'NDS',
        'final_price',
        'unit',
        'kpi',
        'cost',
        'fte',
        'grp'
    )
    search_fields = ('name',)


@admin.register(ResultTable)
class ResultTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'result_list')
