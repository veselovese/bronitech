from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import Building, ImageForEvents, ImageForSpaces, ItemInEvents, ItemInSpaces, Organizer, SpacesReview, User, Registration, Event, Booking, Space, Profile

class RegSerializer(ModelSerializer):
    class Meta:
        model = Registration
        fields = ['id', 'event_id', 'user_id', 'reg_date']
        
class BookSerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'space_id', 'user_id', 'book_date']    
           
class UserProfielSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "patronymic", 'telephone', 'image', "org_status", "admin_status"]
        
class UserShortSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name"]
        
class UserSerializer(ModelSerializer):
    profile = UserProfielSerializer(source='user_profile')
    user_regs = RegSerializer(many=True, read_only=True)
    user_books = BookSerializer(many=True, read_only=True)
    total_events = serializers.IntegerField(read_only=True)
    total_bookings = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", 'profile', 'user_regs', 'user_books', 'total_events', 'total_bookings']

class BookingSerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "user_id", "space_id", 'book_date']
        
class ItemInSpacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInSpaces
        fields = ['id', 'name']

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'city', 'street', 'house']

class ImageForSpacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageForSpaces
        fields = ['id', 'image', 'cover', 'add_date']

class SpacesReviewSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(source='user_id', read_only=True)

    class Meta:
        model = SpacesReview
        fields = ['id', 'review', 'add_date', 'user']
        
class SpaceShortSerializer(ModelSerializer):
    building = BuildingSerializer(source='building_id', read_only=True)

    class Meta:
        model = Space
        fields = ["id", "name", 'description', 'building', 'is_visiable']
        
class SpaceEditSerializer(serializers.ModelSerializer):
    items_id = serializers.PrimaryKeyRelatedField(queryset=ItemInSpaces.objects.all(), many=True)
    building_id = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())

    class Meta:
        model = Space
        fields = ['name', 'description', 'capacity', 'is_visiable', 'building_id', 'items_id']
    
class SpaceSerializer(ModelSerializer):
    bookings = BookSerializer(source='space_books', many=True, read_only=True)
    url = serializers.SerializerMethodField()
    fav_count = serializers.IntegerField(read_only=True)
    building = BuildingSerializer(source='building_id', read_only=True)
    items = ItemInSpacesSerializer(source='items_id', many=True, read_only=True)
    images = ImageForSpacesSerializer(source='space_images', many=True, read_only=True)
    reviews = SpacesReviewSerializer(source='space_reviews', many=True, read_only=True)
    is_fav = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = ["id", "name", 'description', 'capacity', 'building', 'building_id', 'items', 'images', 'bookings', 'url', 'reviews', 'fav_count', 'is_visiable', 'is_fav']
    
    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) if request else obj.get_absolute_url()
    
    def get_is_fav(self, obj):
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
        
    def get_url(self, obj):
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
        
    def get_url(self, obj):
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

    def get_building(self, obj):
        return str(obj.building_id)


class EventWidgetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    organizer = serializers.StringRelatedField()

    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'date', 'image', 'get_absolute_url', 'organizer']

    def get_image(self, obj):
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

    def get_url(self, obj):
        return obj.get_absolute_url()