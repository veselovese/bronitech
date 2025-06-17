import django_filters
from django.db.models import Q, QuerySet
from django.utils import timezone
from datetime import datetime
from typing import Any

from .models import Space, Booking


class SpaceFilter(django_filters.FilterSet):
    """
    Фильтр для модели Space с поддержкой поиска, фильтрации по вместимости, 
    городу, предметам и доступности по датам
    """
    q = django_filters.CharFilter(method='search_filter')
    min_capacity = django_filters.NumberFilter(field_name='capacity', lookup_expr='gte')
    city = django_filters.CharFilter(field_name='building_id__city', lookup_expr='iexact')
    item = django_filters.CharFilter(method='item_filter')
    date_from = django_filters.CharFilter(method='date_filter')
    date_to = django_filters.CharFilter(method='date_filter')

    class Meta:
        model = Space
        fields = ['q', 'min_capacity', 'city', 'item', 'date_from', 'date_to']

    def search_filter(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Фильтрация по имени или описанию помещения

        Args:
            queryset: Начальный набор данных
            name: Имя фильтра
            value: Значение для поиска

        Returns:
            Отфильтрованный QuerySet
        """
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))

    def item_filter(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Фильтрация по имени предмета в помещении

        Args:
            queryset: Начальный набор данных
            name: Имя фильтра
            value: Название предмета.

        Returns:
            Отфильтрованный QuerySet
        """
        return queryset.filter(items_id__name__iexact=value)

    def date_filter(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        """
        Фильтрация помещений по доступности в указанный период времени

        Args:
            queryset: Начальный набор данных
            name: Имя фильтра (date_from или date_to)
            value: Значение даты

        Returns:
            QuerySet, исключающий помещения, занятые в указанный период
        """
        date_from_str = self.data.get('date_from')
        date_to_str = self.data.get('date_to')

        try:
            date_from = timezone.make_aware(datetime.strptime(date_from_str, '%Y-%m-%d %H:%M')) if date_from_str else None
            date_to = timezone.make_aware(datetime.strptime(date_to_str, '%Y-%m-%d %H:%M')) if date_to_str else None
        except ValueError:
            return queryset.none()

        if date_from and date_to and date_from >= date_to:
            return queryset.none()

        if date_from and date_to:
            return queryset.exclude(
                Q(space_books__status=Booking.Status.CONFIRMATION) &
                ~(
                    Q(space_books__date_to__lte=date_from) |
                    Q(space_books__date_from__gte=date_to)
                )
            )
        elif date_from:
            return queryset.exclude(
                Q(space_books__status=Booking.Status.CONFIRMATION) &
                Q(space_books__date_from__lte=date_from) &
                Q(space_books__date_to__gt=date_from)
            )
        elif date_to:
            return queryset.exclude(
                Q(space_books__status=Booking.Status.CONFIRMATION) &
                Q(space_books__date_from__lt=date_to) &
                Q(space_books__date_to__gte=date_to)
            )

        return queryset
