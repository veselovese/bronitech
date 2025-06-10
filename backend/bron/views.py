from urllib import request
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SpacesReview, User, Event, Space, Booking, Organizer, Favourite, Building, ImageForSpaces, ItemInSpaces
from .serializers import SpacesReviewSerializer, UserSerializer, EventSerializer, SpaceSerializer, BookingSerializer, OrganizerSerializer, UserShortSerializer, SpaceShortSerializer, SpaceWidgetSerializer, EventWidgetSerializer, OrganizeWidgetSerializer, SpaceEditSerializer, BuildingSerializer, ImageForSpacesSerializer, ItemInSpacesSerializer
from django.utils import timezone
from datetime import timedelta
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

now = timezone.now()
week_ago = now - timedelta(days=7)

def eventPdfViewSet(request, pk):
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

class IsAdminUserCustom(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'user_profile') and request.user.user_profile.admin_status
    
class UserCurrentViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class UserViewSet(ModelViewSet):
    queryset = User.objects.select_related('user_profile').prefetch_related(
        'user_regs',
        'user_books',
    ).annotate(
        total_events=Count('user_regs', distinct=True),
        total_bookings=Count('user_books', distinct=True)
    ).order_by('-first_name')
    serializer_class = UserSerializer   
    
class UserShortViewSet(ModelViewSet):
    queryset = User.objects.order_by('-first_name')
    serializer_class = UserShortSerializer   
    
class EventViewSet(ModelViewSet):
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
    def week(self, request):
        week_count = Event.objects.filter(date__lte=timezone.now()+timedelta(days=7)).exclude(date__lt=timezone.now()).count()
        data = {
                'week_count': week_count
            }
        return Response(data)
    
class SpaceShortViewSet(ModelViewSet):
    queryset = Space.check_visiable.select_related()
    serializer_class = SpaceShortSerializer

class SpaceHiddenViewSet(ModelViewSet):
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

class SpaceViewSet(ModelViewSet):
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
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
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
    def search(self, request):
        search = request.GET.get('q', '')
        if search:
            spaces = Space.check_visiable.select_related(
        'building_id'
    ).prefetch_related(
        'items_id',
        'space_images',
        'space_reviews',
        'space_reviews__user_id',
        'space_books'
    ).annotate(
        fav_count=Count('favourite')
    ).filter( Q(name__icontains=search) |
                Q(description__icontains=search))
        else:
            spaces = Space.check_visiable.none()
        return Response(SpaceSerializer(spaces, many=True, context={'request': request}).data)
      
    @action(detail=False, methods=['get'])
    def short(self, request):
        spaces = Space.check_visiable.values_list('id', 'name')
        return Response(spaces)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favourite(self, request, pk=None):
        user = request.user
        space = self.get_object()

        fav, created = Favourite.objects.get_or_create(user_id=user, space_id=space)
        if not created:
            fav.delete()
            return Response({'status': 'removed'})
        return Response({'status': 'added'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        space = self.get_object()
        user = request.user
        review_text = request.data.get('review')

        if not review_text:
            return Response({'error': 'Комментарий не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)

        review = SpacesReview.objects.create(
            user_id=user,
            space_id=space,
            review=review_text
        )
        return Response(SpacesReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated], url_path='delete_review/(?P<review_id>[^/.]+)')
    def delete_review(self, request, pk=None, review_id=None):
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
    def update_review(self, request, pk=None, review_id=None):
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
    def edit_space(self, request, pk=None):
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
    
    # @action(detail=True, methods=['post'], url_path='create', permission_classes=[IsAuthenticated])
    # def create_space(self, request):
    #     create_space = request.data.get('space')
        
    #     if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
    #         return Response({'detail': 'Нет прав на создание'}, status=status.HTTP_403_FORBIDDEN)
        
    #     if not create_space:
    #         return Response({'error': 'Информация о помещении не может быть пустой'}, status=status.HTTP_400_BAD_REQUEST)

    #     serializer = SpaceSerializer(create_space)
    #     if serializer.is_valid():
    #         space = serializer.save()
    #         return Response(SpaceSerializer(space).data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='images')
    def upload_image(self, request, pk=None):
        space = self.get_object()
        if not request.user.is_authenticated or not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Нет прав на редактирование'}, status=403)

        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image provided'}, status=400)

        new_image = ImageForSpaces.objects.create(space_id=space, image=image)
        return Response(ImageForSpacesSerializer(new_image).data)
    
    @action(detail=True, methods=['delete'], url_path='delete_image/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        try:
            image = ImageForSpaces.objects.get(id=image_id, space_id=pk)
        except ImageForSpaces.DoesNotExist:
            return Response({'detail': 'Изображение не найдено'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'user_profile') or not request.user.user_profile.admin_status:
            return Response({'detail': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        image.delete()
        return Response({'detail': 'Изображение удалено'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='set_cover/(?P<image_id>[^/.]+)')
    def set_cover(self, request, pk=None, image_id=None):
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


class BookingViewSet(ModelViewSet):
    queryset = Booking.objects.select_related(
        'user_id',
        'space_id'
    )
    serializer_class = BookingSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        book_stats = Booking.objects.filter(
            book_date__range=(week_ago, now)
        ).aggregate(last_week_bookings=Count('id'))
        return Response(book_stats)
    
class OrganizerViewSet(ModelViewSet):
    queryset = Organizer.objects.select_related()
    serializer_class = OrganizerSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.GET.get('q', '')
        if query:
            orgs = Organizer.objects.filter(name__contains=query)
        else:
            orgs = Organizer.objects.none()
        return Response(SpaceSerializer(orgs, many=True).data)
    
    @action(detail=False, methods=['get'])
    def short(self, request):
        orgs = Organizer.objects.values('id', 'name')
        return Response(orgs)
     
class SpacesReviewViewSet(ModelViewSet):
    queryset = SpacesReview.objects.select_related()
    serializer_class = SpacesReviewSerializer
    
class WidgetViewSet(ViewSet):
    @action(detail=False, methods=["get"])
    def homepage(self, request):
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
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    
class ItemsInSpacesViewSet(ModelViewSet):
    queryset = ItemInSpaces.objects.all()
    serializer_class = ItemInSpacesSerializer
    
