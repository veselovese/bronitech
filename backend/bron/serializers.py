from typing import Optional
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import *

class ExamSerializer(ModelSerializer):
    class Meta:
        model = mvexam
        fields = ['id', 'exam_name', 'created_date', 'exam_date', 'users', 'is_public']    
        
class RegSerializer(ModelSerializer):
    class Meta:
        model = Registration
        fields = ['id', 'event_id', 'user_id', 'reg_date']    
           
class UserProfielSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "patronymic", 'telephone', 'image', "org_status", "admin_status"]
        
class UserShortSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name"]
        
class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'city', 'street', 'house']
        
class ImageForSpacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageForSpaces
        fields = ['id', 'image', 'cover', 'add_date']        
        
class SpaceShortSerializer(ModelSerializer):
    building = BuildingSerializer(source='building_id', read_only=True)
    images = ImageForSpacesSerializer(source='space_images', many=True, read_only=True)

    class Meta:
        model = Space
        fields = ["id", "name", 'description', 'building', 'is_visiable', 'images']
        
class BookingSerializer(ModelSerializer):
    user = UserShortSerializer(source='user_id', read_only=True)
    space = SpaceShortSerializer(source='space_id', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'space_id', 'space', 'user_id', 'user', 'date_from', 'date_to', 'book_date', 'status']
        
class UserSerializer(ModelSerializer):
    profile = UserProfielSerializer(source='user_profile')
    user_regs = RegSerializer(many=True, read_only=True)
    user_books = BookingSerializer(many=True, read_only=True)
    total_events = serializers.IntegerField(read_only=True)
    total_bookings = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", 'username', 'email', 'profile', 'user_regs', 'user_books', 'total_events', 'total_bookings']
        
class ItemInSpacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInSpaces
        fields = ['id', 'name']

class SpacesReviewSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(source='user_id', read_only=True)

    class Meta:
        model = SpacesReview
        fields = ['id', 'review', 'add_date', 'user']
        
class SpaceEditSerializer(serializers.ModelSerializer):
    items_id = serializers.PrimaryKeyRelatedField(queryset=ItemInSpaces.objects.all(), many=True)
    building_id = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

    class Meta:
        model = Space
        fields = ['name', 'description', 'capacity', 'is_visiable', 'building_id', 'items_id']
    
class SpaceSerializer(ModelSerializer):
    bookings = BookingSerializer(source='space_books', many=True, read_only=True)
    url = serializers.SerializerMethodField()
    fav_count = serializers.IntegerField(read_only=True)
    building = BuildingSerializer(source='building_id', read_only=True)
    items = ItemInSpacesSerializer(source='items_id', many=True, read_only=True)
    images = ImageForSpacesSerializer(source='space_images', many=True, read_only=True)
    reviews = SpacesReviewSerializer(source='space_reviews', many=True, read_only=True)
    is_fav = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = ["id", "name", 'description', 'capacity', 'building', 'building_id', 'items', 'items_id', 'images', 'bookings', 'url', 'reviews', 'fav_count', 'is_visiable', 'is_fav']
    
    def get_url(self, obj: Space) -> str:
        """
        Получение полного URL объекта Space

        Args:
            obj: Объект Space

        Returns:
            Абсолютный URL объекта
        """
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) if request else obj.get_absolute_url()
    
    def get_is_fav(self, obj: Space) -> bool:
        """
        Проверяет, является ли пространство любимым для текущего пользователя

        Args:
            obj: Объект Space

        Returns:
            True, если пространство добавлено в избранное текущим пользователем, иначе False
        """
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favourite.filter(user_id=user).exists()
        return False
    
class OrganizerSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    user = UserShortSerializer(source='org_id', read_only=True)

    class Meta:
        model = Organizer
        fields = ['id', 'name', 'description', 'user', 'url']
        
    def get_url(self, obj: Organizer) -> str:
        """
        Получение полного URL объекта Organizer

        Args:
            obj: Объект Organizer

        Returns:
            Абсолютный URL объекта
        """
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) if request else obj.get_absolute_url()

class ItemInEventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInEvents
        fields = ['id', 'name']

class ImageForEventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageForEvents
        fields = ['id', 'image', 'cover']

class EventSerializer(ModelSerializer):
    url = serializers.SerializerMethodField()
    regs = RegSerializer(source='event_reg', many=True, read_only=True)
    reg_count = serializers.IntegerField(read_only=True)
    organizer = OrganizerSerializer(source='org_id', read_only=True)
    space = SpaceShortSerializer(source='space_id', read_only=True)
    items = ItemInEventsSerializer(source='items_id', many=True, read_only=True)
    images = ImageForEventsSerializer(source='event_images', many=True, read_only=True)
        
    class Meta:
        model = Event
        fields = ["id", "name", 'description', 'date', 'org_id', 'organizer', 'space_id', 'space', 'images', 'items', 'regs', 'url', 'reg_count', 'is_visiable']
        
    def get_url(self, obj: Event) -> str:
        """
        Получение полного URL объекта Event

        Args:
            obj: Объект Event

        Returns:
            Абсолютный URL объекта
        """
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) if request else obj.get_absolute_url()
    
class SpaceWidgetSerializer(serializers.ModelSerializer):
    images = ImageForSpacesSerializer(source='space_images', many=True, read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    fav_count = serializers.IntegerField(read_only=True)
    booking_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Space
        fields = ['id', 'name', 'add_date', 'images', 'get_absolute_url', 'review_count', 'fav_count', 'booking_count']

    def get_building(self, obj: Space) -> str:
        """
        Возвращает строковое представление здания, связанного с пространством

        Args:
            obj: Объект Space

        Returns:
            Строковое представление здания
        """
        return str(obj.building_id)


class EventWidgetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    organizer = serializers.StringRelatedField()

    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'date', 'image', 'get_absolute_url', 'organizer']

    def get_image(self, obj: Event) -> Optional[str]:
        """
        Получает URL изображения с пометкой cover, либо первое изображение, либо None

        Args:
            obj: Объект Event

        Returns:
            URL изображения или None
        """
        cover = obj.event_images.filter(cover=True).first()
        if cover:
            return cover.image.url
        img = obj.event_images.first()
        return img.image.url if img else None
    
class OrganizeWidgetSerializer(serializers.ModelSerializer):
    event_count = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Organizer
        fields = ['id', 'name', 'description', 'event_count', 'url']

    def get_url(self, obj: Organizer) -> str:
        """
        Получение абсолютного URL объекта Organizer

        Args:
            obj: Объект Organizer

        Returns:
            Абсолютный URL объекта
        """
        return obj.get_absolute_url()