from typing import Any, Optional
from urllib import request
from django.shortcuts import get_object_or_404, render
from requests import Request
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import ExamSerializer, SpacesReviewSerializer, UserSerializer, EventSerializer, SpaceSerializer, BookingSerializer, OrganizerSerializer, UserShortSerializer, SpaceShortSerializer, SpaceWidgetSerializer, EventWidgetSerializer, OrganizeWidgetSerializer, SpaceEditSerializer, BuildingSerializer, ImageForSpacesSerializer, ItemInSpacesSerializer
from django.utils import timezone
from django.db.models import Count, Q, ExpressionWrapper, IntegerField, F
from django.http import HttpResponse, Http404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
import os
import qrcode
import io
from django.conf import settings
from django.utils.timezone import localtime
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .filters import SpaceFilter

now = timezone.now()
week_ago = now - timedelta(days=7)

def eventPdfViewSet(request: HttpResponse, pk: int) -> HttpResponse:
    """
    Генерация PDF-документа с информацией о мероприятии

    Args:
        request: Объект запроса
        pk: ID мероприятия

    Returns:
        PDF-файл в HTTP-ответе
    """
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        raise Http404("Мероприятие не найдено")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="event_{event.pk}.pdf"'
    
    font_path = os.path.join(settings.BASE_DIR, 'bron', 'static', 'fonts', 'Gilroy-Regular.ttf')
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден: {font_path}")
    
    pdfmetrics.registerFont(TTFont('Gilroy', font_path))
    
    font_path = os.path.join(settings.BASE_DIR, 'bron', 'static', 'fonts', 'Gilroy-Bold.ttf')
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден: {font_path}")
    
    pdfmetrics.registerFont(TTFont('Gilroy-Bold', font_path))

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 3 * cm

    p.setFont("Gilroy", 12)
    p.setFillColor(colors.darkblue)
    p.drawString(2 * cm, y, f"Сводка по мероприятию")
    y -= 1 * cm
    
    p.setFont("Gilroy-Bold", 24)
    p.setFillColor(colors.darkblue)
    p.drawString(2 * cm, y, f"{event.name}")
    y -= 1.25 * cm
    
    p.setFillColor(colors.black)
    p.setFont("Gilroy", 12)
    p.drawString(2 * cm, y, f"{event.description}")
    y -= 2 * cm
    
    months = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    localized_date = localtime(event.date)
    day = localized_date.day
    month = months[localized_date.month]
    year = localized_date.year
    time = localized_date.strftime("%H:%M")

    formatted_date = f"{day} {month} {year}"

    p.setFont("Gilroy-Bold", 16)
    p.setFillColor(colors.black)
    p.drawString(2 * cm, y, f"{formatted_date}")
    y -= 0.5 * cm
    
    p.setFont("Gilroy", 8)
    p.setFillColor(colors.grey)
    p.drawString(2 * cm, y, f"дата")
    y += 0.5 * cm
    
    p.setFont("Gilroy-Bold", 16)
    p.setFillColor(colors.black)
    p.drawString(7 * cm, y, f"{time}")
    y -= 0.5 * cm
    
    p.setFont("Gilroy", 8)
    p.setFillColor(colors.grey)
    p.drawString(7 * cm, y, f"время")
    y += 0.5 * cm

    p.setFont("Gilroy-Bold", 16)
    p.setFillColor(colors.black)
    space_name = event.space_id.name if event.space_id else '—'
    p.drawString(10 * cm, y, f"{space_name}")
    y -= 0.5 * cm
    
    p.setFont("Gilroy", 8)
    p.setFillColor(colors.grey)
    space_address = event.space_id.building_id.city + ', ' + event.space_id.building_id.street + ', ' + event.space_id.building_id.house if event.space_id.building_id else '—'
    p.drawString(10 * cm, y, f"{space_address}")
    y -= 1 * cm

    p.setFont("Gilroy-Bold", 16)
    p.setFillColor(colors.black)
    org_name = event.org_id.name if event.org_id else '—'
    p.drawString(2 * cm, y, f"{org_name}")
    y -= 0.5 * cm
    
    p.setFont("Gilroy", 8)
    p.setFillColor(colors.grey)
    p.drawString(2 * cm, y, f"организатор")
    y -=  6* cm
    
    qr_url = f"http://127.0.0.1:8080/events/{event.pk}"
    qr = qrcode.make(qr_url)
    qr_io = io.BytesIO()
    qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    p.drawImage(ImageReader(qr_io), 1.5 * cm, y, width=5 * cm, height=5 * cm, mask=None)
    p.drawString(2 * cm, y, f"подробности")
    
    qr_url = f"http://127.0.0.1:8080/regs/{event.pk}"
    qr = qrcode.make(qr_url)
    qr_io = io.BytesIO()
    qr.save(qr_io, format='PNG')
    qr_io.seek(0)

    p.drawImage(ImageReader(qr_io), 7.5 * cm, y, width=5 * cm, height=5 * cm, mask=None)
    p.drawString(8 * cm, y, f"регистрация")
    y -=  2* cm

    if hasattr(event, 'items_id'):
        p.setFont("Gilroy", 12)
        p.setFillColor(colors.black)
        for item in event.items_id.all():
            p.drawString(2 * cm, y, f"#{item.name}")
            y -= 0.5 * cm
            if y < 3 * cm:
                p.showPage()
                y = height - 3 * cm

    y -= 0.5 * cm

    p.setFont("Gilroy", 8)
    p.setFillColor(colors.grey)
    p.drawString(2 * cm, 1.5 * cm, "Сформировано автоматически")

    p.showPage()
    p.save()

    return response

class ExamViewSet(ModelViewSet):
    queryset = mvexam.objects.filter(is_public=True).order_by('-exam_date')
    serializer_class = ExamSerializer

class IsAdminUserCustom(permissions.BasePermission):
    """
    Проверка, является ли пользователь админом
    """
    def has_permission(self, request, view) -> bool:
        """
        Проверка прав доступа

        Args:
            request: Объект запроса
            view: Представление

        Returns:
            True, если пользователь аутентифицирован и является админом
        """
        return request.user.is_authenticated and hasattr(request.user, 'user_profile') and request.user.user_profile.admin_status
    
class UserCurrentViewSet(APIView):
    """
    Возвращает текущего авторизованного пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpResponse) -> Response:
        """
        Получить данные текущего пользователя

        Args:
            request: Объект запроса

        Returns:
            Сериализованные данные пользователя
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class UserAdminViewSet(APIView):
    """
    Представление для получения списка пользователей, кроме текущего админа
    """
    permission_classes = [IsAdminUserCustom]

    def get(self, request: HttpResponse) -> Response:
        """
        Получить список пользователей с подсчетом мероприятий и бронирований

        Args:
            request: Объект запроса

        Returns:
            Список сериализованных пользователей
        """
        user = request.user
        users = User.objects.select_related('user_profile').prefetch_related(
            'user_regs',
            'user_books',
        ).annotate(
            total_events=Count('user_regs', distinct=True),
            total_bookings=Count('user_books', distinct=True)
        ).exclude(
            id=user.id,
        ).order_by(
            'first_name'
        )
        return Response(UserSerializer(users, many=True).data)
    
class UserMakeAdminViewSet(ModelViewSet):
    """
    Представление для управления правами администратора пользователей
    """
    permission_classes = [IsAuthenticated, IsAdminUserCustom]
    queryset = User.objects.select_related('user_profile').prefetch_related(
        'user_regs',
        'user_books',
    ).annotate(
        total_events=Count('user_regs', distinct=True),
        total_bookings=Count('user_books', distinct=True)
    ).order_by('-first_name')
    serializer_class = UserSerializer 
    
    @action(detail=True, methods=['patch', 'get'], permission_classes=[IsAdminUserCustom])
    def makeadmin(self, request: HttpResponse, pk: int = None) -> Response:
        """
        Назначить пользователя админом

        Args:
            request: Объект запроса
            pk: ID пользователя

        Returns:
            Сериализованные данные пользователя
        """
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        user.user_profile.admin_status = True
        user.save()
        
        users = User.objects.select_related('user_profile').prefetch_related(
            'user_regs',
            'user_books',
        ).annotate(
            total_events=Count('user_regs', distinct=True),
            total_bookings=Count('user_books', distinct=True)
        ).exclude(
            id=user.id,
        ).order_by(
            'first_name'
        )

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)  
    
    @action(detail=True, methods=['patch', 'get'], permission_classes=[IsAdminUserCustom])
    def unmakeadmin(self, request: HttpResponse, pk: int = None) -> Response:
        """
        Убрать у пользователя права админа

        Args:
            request: Объект запроса
            pk: ID пользователя

        Returns:
            Сериализованные данные пользователя
        """
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        user.user_profile.admin_status = False
        user.save()
        
        users = User.objects.select_related('user_profile').prefetch_related(
            'user_regs',
            'user_books',
        ).annotate(
            total_events=Count('user_regs', distinct=True),
            total_bookings=Count('user_books', distinct=True)
        ).exclude(
            id=user.id,
        ).order_by(
            'first_name'
        )

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)  
    
class UserViewSet(ModelViewSet):
    """
    Представление для пользователей с полной информацией
    """
    permission_classes = [IsAuthenticated]
    queryset = User.objects.select_related('user_profile').prefetch_related(
        'user_regs',
        'user_books',
    ).annotate(
        total_events=Count('user_regs', distinct=True),
        total_bookings=Count('user_books', distinct=True)
    ).order_by('-first_name')
    serializer_class = UserSerializer   
    
class UserShortViewSet(ModelViewSet):
    """
    Представление для краткого списка пользователей
    """
    queryset = User.objects.order_by('-first_name')
    serializer_class = UserShortSerializer   
    
class EventViewSet(ModelViewSet):
    """
    Представление для управления мероприятиями
    """
    queryset = Event.objects.select_related(
    ).prefetch_related(
        'items_id',
        'event_images',
        'event_regs'
    ).annotate(
        reg_count=Count('event_regs')).prefetch_related('event_regs').filter(
            is_visiable=True).exclude(date__lt=timezone.now()).order_by('-reg_count')
    serializer_class = EventSerializer   
    
    @action(detail=False, methods=['get'])
    def week(self, request: HttpResponse) -> Response:
        """
        Получить количество мероприятий за текущую неделю

        Args:
            request: Объект запроса

        Returns:
            Словарь с количеством мероприятий
        """
        week_count = Event.objects.filter(date__lte=timezone.now()+timedelta(days=7)).exclude(date__lt=timezone.now()).count()
        data = {
                'week_count': week_count
            }
        return Response(data)
    
class SpaceShortViewSet(ModelViewSet):
    """
    Представление для краткого списка пространств
    """
    queryset = Space.check_visiable.select_related()
    serializer_class = SpaceShortSerializer

class SpaceHiddenViewSet(ModelViewSet):
    """
    Представление для скрытых пространств
    """
    queryset = Space.objects.select_related(
        ).prefetch_related(
            'items_id', 
            'space_images',
            'space_reviews',
            'favourite',
            'space_reviews__user_id',
            'space_books'
        ).annotate(
            fav_count=Count('favourite')
        ).order_by('-fav_count').filter(is_visiable=False)
        
    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated, IsAdminUserCustom]
    
    @action(detail=True, methods=['post'], url_path='images')
    def upload_image(self, request: HttpResponse, pk: int = None) -> Response:
        """
        Загрузить изображение к пространству

        Args:
            request: Объект запроса
            pk: ID пространства

        Returns:
            Сериализованное изображение или сообщение об ошибке
        """
        space = self.get_object()
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Нет прав на редактирование'}, status=403)

        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image provided'}, status=400)

        new_image = ImageForSpaces.objects.create(space_id=space, image=image)
        return Response(ImageForSpacesSerializer(new_image).data)
    
    @action(detail=True, methods=['delete'], url_path='delete_image/(?P<image_id>[^/.]+)')
    def delete_image(self, request: HttpResponse, pk: int = None, image_id: int = None) -> Response:
        """
        Удалить изображение у пространства

        Args:
            request: Объект запроса
            pk: ID пространства
            image_id: ID изображения

        Returns:
            Подтверждение удаления или сообщение об ошибке
        """
        try:
            image = ImageForSpaces.objects.get(id=image_id, space_id=pk)
        except ImageForSpaces.DoesNotExist:
            return Response({'detail': 'Изображение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        image.delete()
        return Response({'detail': 'Изображение удалено'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='set_cover/(?P<image_id>[^/.]+)')
    def set_cover(self, request: HttpResponse, pk: int = None, image_id: int = None) -> Response:
        """
        Установить обложку для изображения пространства

        Args:
            request: Объект запроса
            pk: ID пространства
            image_id: ID изображения

        Returns:
            Сериализованные данные изображения
        """
        try:
            image = ImageForSpaces.objects.get(id=image_id, space_id=pk)
        except ImageForSpaces.DoesNotExist:
            return Response({'detail': 'Изображение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        ImageForSpaces.objects.filter(space_id=pk, cover=True).update(cover=False)

        image.cover = True
        image.save()

        return Response(ImageForSpacesSerializer(image).data, status=status.HTTP_200_OK)

class SpaceViewSet(ModelViewSet):
    """
    ViewSet для управления пространствами
    """
    queryset = Space.check_visiable.select_related(
        ).prefetch_related(
            'items_id', 
            'space_images',
            'space_reviews',
            'favourite',
            'space_reviews__user_id',
            'space_books'
        ).annotate(
            fav_count=Count('favourite')
        ).order_by('-fav_count')
        
    serializer_class = SpaceSerializer
    
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpaceFilter
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Создание нового пространства

        Args:
            request: Объект запроса

        Returns:
            Response: Ответ API
        """
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def stats(self, request: Request) -> Response:
        """
        Получение статистики: наиболее бронируемое пространство за последнюю неделю

        Args:
            request: Объект запроса

        Returns:
            Response: Ответ API со статистикой
        """
        most_booked_space = Space.check_visiable.annotate(
            book_count=Count('space_books',
            filter=Q(space_books__book_date__range=(week_ago, now)))
        ).order_by('-book_count').first()

        if most_booked_space and most_booked_space.book_count > 0:
            data = {
                'most_booked_space_id': most_booked_space.id,
                'most_booked_space_name': most_booked_space.name,
                'most_booked_count': most_booked_space.book_count,
            }
        else:
            data = {
                'space_id': None,
                'space_name': None,
                'book_count': 0,
            }
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def items(self, request: Request) -> Response:
        """
        Список всех предметов в пространствах

        Returns:
            Response: Список предметов
        """
        items = ItemInSpaces.objects.values('id', 'name')
        return Response(items)
    
    @action(detail=False, methods=['get'])
    def search(self, request: Request) -> Response:
        """
        Поиск по фильтру

        Returns:
            Response: Отфильтрованные пространства
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
      
    @action(detail=False, methods=['get'])
    def short(self, request: Request) -> Response:
        """
        Краткая информация: id и name всех пространств

        Returns:
            Response: Краткий список пространств
        """
        spaces = Space.check_visiable.values_list('id', 'name')
        return Response(spaces)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favourite(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Добавление или удаление пространства из избранного

        Args:
            pk: ID пространства

        Returns:
            Response: Статус действия
        """
        user = request.user
        space = self.get_object()

        fav, created = Favourite.objects.get_or_create(user_id=user, space_id=space)
        if not created:
            fav.delete()
            return Response({'status': 'removed'})
        return Response({'status': 'added'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_comment(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Добавить комментарий к пространству (если было бронирование)

        Args:
            pk: ID пространства

        Returns:
            Response: Новый отзыв или ошибка
        """
        space = self.get_object()
        user = request.user
        review_text = request.data.get('review')

        if not review_text:
            return Response({'error': 'Комментарий не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)

        has_booking = Booking.objects.filter(
                user_id=user,
                space_id=space,
                status=Booking.Status.CONFIRMATION
            ).exists()
        
        if not has_booking:
            return Response({'error': 'Вы не можете оставить отзыв, так как не бронировали это помещение'},
                        status=status.HTTP_403_FORBIDDEN)

        review = SpacesReview.objects.create(
            user_id=user,
            space_id=space,
            review=review_text
        )
        return Response(SpacesReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated], url_path='delete_review/(?P<review_id>[^/.]+)')
    def delete_review(self, request: Request, pk: Optional[str] = None, review_id: Optional[str] = None) -> Response:
        """
        Удалить отзыв пользователя

        Args:
            pk: ID пространства
            review_id: ID отзыва

        Returns:
            Response: Статус удаления
        """
        user = request.user
        try:
            review = SpacesReview.objects.get(id=review_id, space_id=pk)
        except SpacesReview.DoesNotExist:
            return Response({'error': 'Отзыв не найден'}, status=status.HTTP_404_NOT_FOUND)

        if review.user_id != user:
            return Response({'error': 'Вы не можете удалить этот отзыв'}, status=status.HTTP_403_FORBIDDEN)

        review.delete()
        return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['put'], url_path='update_review/(?P<review_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def update_review(self, request: Request, pk: Optional[str] = None, review_id: Optional[str] = None) -> Response:
        """
        Обновить отзыв пользователя

        Args:
            pk: ID пространства
            review_id: ID отзыва
            request: Объект запроса

        Returns:
            Response: Отредактированный отзыв или ошибка
        """
        update_review = request.data.get('review')
        try:
            review = SpacesReview.objects.get(id=review_id, space_id=pk)
        except SpacesReview.DoesNotExist:
            return Response({'detail': 'Комментарий не найден'}, status=status.HTTP_404_NOT_FOUND)

        if review.user_id != request.user:
            return Response({'detail': 'Нет прав на редактирование'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SpacesReviewSerializer(review, data=update_review, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], url_path='edit', permission_classes=[IsAuthenticated])
    def edit_space(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Редактирование информации о пространстве

        Args:
            pk: ID пространства
            request: Объект запроса

        Returns:
            Response: Отредактированное пространство или ошибка
        """
        update_space = request.data.get('space')
        try:
            space = Space.objects.get(id=pk)
        except SpacesReview.DoesNotExist:
            return Response({'detail': 'Помещение не найдено'}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Нет прав на редактирование'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SpaceEditSerializer(space, data=update_space, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='images')
    def upload_image(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Загрузить изображение для пространства

        Args:
            pk: ID пространства
            request: Объект запроса

        Returns:
            Response: Данные загруженного изображения или ошибка
        """
        space = self.get_object()
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Нет прав на редактирование'}, status=403)

        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image provided'}, status=400)

        new_image = ImageForSpaces.objects.create(space_id=space, image=image)
        return Response(ImageForSpacesSerializer(new_image).data)
    
    @action(detail=True, methods=['delete'], url_path='delete_image/(?P<image_id>[^/.]+)')
    def delete_image(self, request: Request, pk: Optional[str] = None, image_id: Optional[str] = None) -> Response:
        """
        Удалить изображение пространства

        Args:
            pk: ID пространства
            image_id: ID изображения
            request: Объект запроса

        Returns:
            Response: Статус удаления или ошибка
        """
        try:
            image = ImageForSpaces.objects.get(id=image_id, space_id=pk)
        except ImageForSpaces.DoesNotExist:
            return Response({'detail': 'Изображение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        image.delete()
        return Response({'detail': 'Изображение удалено'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='set_cover/(?P<image_id>[^/.]+)')
    def set_cover(self, request: Request, pk: Optional[str] = None, image_id: Optional[str] = None) -> Response:
        """
        Установить изображение обложкой пространства

        Args:
            pk: ID пространства
            image_id: ID изображения
            request: Объект запроса

        Returns:
            Response: Данные обложки или ошибка
        """
        try:
            image = ImageForSpaces.objects.get(id=image_id, space_id=pk)
        except ImageForSpaces.DoesNotExist:
            return Response({'detail': 'Изображение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        ImageForSpaces.objects.filter(space_id=pk, cover=True).update(cover=False)

        image.cover = True
        image.save()

        return Response(ImageForSpacesSerializer(image).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='book')
    def book(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Забронировать пространство

        Args:
            pk: ID пространства
            request: Объект запроса с датами брони

        Returns:
            Response: Данные бронирования или ошибка
        """
        space = self.get_object()
        user = request.user

        try:
            date_from = timezone.make_aware(datetime.strptime(request.data.get('date_from'), '%Y-%m-%d %H:%M'))
            date_to = timezone.make_aware(datetime.strptime(request.data.get('date_to'), '%Y-%m-%d %H:%M'))
        except Exception:
            return Response({'error': 'Неверный формат даты'}, status=400)

        if date_from >= date_to:
            return Response({'error': 'Дата начала должна быть раньше даты окончания'}, status=400)

        conflict_qs = Booking.objects.filter(
            space_id=space,
            status=Booking.Status.CONFIRMATION
        )

        if date_from and date_to:
            conflict_qs = conflict_qs.exclude(
                Q(date_to__lte=date_from) |
                Q(date_from__gte=date_to)
            )
        elif date_from:
            conflict_qs = conflict_qs.filter(
                date_from__lte=date_from,
                date_to__gt=date_from
            )
        elif date_to:
            conflict_qs = conflict_qs.filter(
                date_from__lt=date_to,
                date_to__gte=date_to
            )

        if conflict_qs.exists():
            return Response({'error': 'Помещение занято в выбранный период'}, status=400)

        new_book = Booking.objects.create(
            user_id=user,
            space_id=space,
            date_from=date_from,
            date_to=date_to,
        )

        return Response(BookingSerializer(new_book).data, status=201)

class BookingViewSet(ModelViewSet):
    """
    ViewSet для управления бронированиями
    """
    queryset = Booking.objects.select_related()
    serializer_class = BookingSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request: Request) -> Response:
        """
        Получить статистику бронирований за последнюю неделю

        Args:
            request: Объект запроса

        Returns:
            Response: Статистика бронирований
        """
        book_stats = Booking.objects.filter(
            book_date__range=(week_ago, now)
        ).aggregate(last_week_bookings=Count('id'))
        return Response(book_stats)
    
class NewBookingViewSet(ModelViewSet):
    """
    ViewSet для управления новыми бронированиями
    """
    permission_classes = [IsAdminUserCustom]
    queryset = Booking.objects.select_related().filter(
                status="NB",
                date_from__gte=timezone.now()
            ).order_by('book_date')
    serializer_class = BookingSerializer
    
    @action(detail=True, methods=['patch', 'get'], permission_classes=[IsAdminUserCustom])
    def conf(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Подтвердить бронирование

        Args:
            pk: ID бронирования
            request: Объект запроса

        Returns:
            Response: Обновленный список новых бронирований или ошибка
        """
        try:
            book = Booking.objects.get(id=pk)
        except Booking.DoesNotExist:
            return Response({'detail': 'Бронирование не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        book.status = "C"
        book.save()
        
        books = Booking.objects.select_related().filter(
                status="NB",
                date_from__gte=timezone.now()
            )

        return Response(BookingSerializer(books, many=True).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch', 'get'], permission_classes=[IsAdminUserCustom])
    def canc(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Отменить бронирование

        Args:
            pk: ID бронирования.
            request: Объект запроса

        Returns:
            Response: Обновленный список новых бронирований или ошибка
        """
        try:
            book = Booking.objects.get(id=pk)
        except Booking.DoesNotExist:
            return Response({'detail': 'Бронирование не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        book.status = "CBC"
        book.save()
        
        books = Booking.objects.select_related().filter(
                status="NB",
                date_from__gte=timezone.now()
            )

        return Response(BookingSerializer(books, many=True).data, status=status.HTTP_200_OK)
          
class OrganizerViewSet(ModelViewSet):
    """
    ViewSet для управления организаторами
    """
    queryset = Organizer.objects.select_related()
    serializer_class = OrganizerSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request: Request) -> Response:
        """
        Поиск организаторов по части имени

        Args:
            request: запрос с параметром 'q' для поиска по имени

        Returns:
            Response с сериализованным списком найденных организаторов
        """
        query = request.GET.get('q', '')
        if query:
            orgs = Organizer.objects.filter(name__contains=query)
        else:
            orgs = Organizer.objects.none()
        return Response(SpaceSerializer(orgs, many=True).data)
    
    @action(detail=False, methods=['get'])
    def short(self, request: Request) -> Response:
        """
        Получение краткого списка организаторов

        Args:
            request: запрос

        Returns:
            Response с кратким списком организаторов
        """
        orgs = Organizer.objects.values('id', 'name')
        return Response(orgs)
     
class SpacesReviewViewSet(ModelViewSet):
    """
    ViewSet для управления отзывами помещений
    """
    queryset = SpacesReview.objects.select_related()
    serializer_class = SpacesReviewSerializer
    
class WidgetViewSet(ViewSet):
    """
    ViewSet для управления виджетами на главной странице
    """
    @action(detail=False, methods=["get"])
    def homepage(self, request: Request) -> Response:
        """
        Получение данных для главной страницы: топ популярных помещений,
        ближайших мероприятий и организаторов

        Args:
            request: запрос

        Returns:
            Response с тремя списками: популярных помещений,
            предстоящих событий и топ организаторов
        """
        spaces = Space.objects.annotate(
            review_count=Count('space_reviews', filter=Q(space_reviews__is_visiable=True), distinct=True),
            fav_count=Count('favourite', distinct=True),
            booking_count=Count('space_books', filter=Q(space_books__status='C'), distinct=True)
        )
        
        spaces = spaces.annotate(
        popularity_score=ExpressionWrapper(
        F('review_count') + F('fav_count') + F('booking_count'),
        output_field=IntegerField()
            )
        )

        top_popular = spaces.order_by('-popularity_score')[:3]

        upcoming_events = Event.objects.filter(
            date__gte=timezone.now(), is_visiable=True
        ).order_by('date')[:3]
        
        organizers = Organizer.objects.annotate(
            event_count=Count('org_events', distinct=True)
        ).order_by('-event_count')[:3]
        
        return Response({
            "top_popular_spaces": SpaceWidgetSerializer(top_popular, many=True).data,
            "upcoming_events": EventWidgetSerializer(upcoming_events, many=True).data,
            "top_organizers": OrganizeWidgetSerializer(organizers, many=True).data
        })
        
class BuildingViewSet(ModelViewSet):
    """
    ViewSet для управления зданиями
    """
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    
    @action(detail=False, methods=['get'])
    def cities(self, request: Request) -> Response:
        """
        Получение списка уникальных городов из зданий

        Args:
            request: запрос

        Returns:
            Response со списком уникальных городов
        """
        cities = Building.objects.values_list('city').distinct()
        return Response(cities)
    
class ItemsInSpacesViewSet(ModelViewSet):
    """
    ViewSet для управления особенностями помещений
    """
    queryset = ItemInSpaces.objects.all()
    serializer_class = ItemInSpacesSerializer
    
