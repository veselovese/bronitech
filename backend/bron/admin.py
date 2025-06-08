from django.contrib import admin, messages
from bron.models import *
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from datetime import timedelta
from django.db.models import Q 

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('profile_link', 'first_name', 'second_name', 'patronymic', 'email', 'telephone', 'link_tag', 'org_status')
    list_display_links = None
    list_filter = ('org_status',)
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'patronymic']
    
    @admin.display(description='Имя пользователя')
    def profile_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.user.username))
    
    @admin.display(description='Имя')
    def first_name(self, obj):
        return obj.user.first_name
    
    @admin.display(description='Фамилия')
    def second_name(self, obj):
        return obj.user.last_name
    
    @admin.display(description='Почта')
    def email(self, obj):
        return obj.user.email
    
    @admin.display(description='Telegram')
    def link_tag(self, obj):
        if (obj.telegram_link != None):
            return format_html('<a href="{}" target="_blank">{}</a>', obj.telegram_link, obj.telegram_link)
        return '-'
    
class ProfileInline(admin.TabularInline): 
    model = Profile
    extra = 0     

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'patronymic', 'email', 'telephone', 'org_status')
    inlines = [ProfileInline]
    
    @admin.display(description='Отчество')
    def patronymic(self, obj):
        return obj.user_profile.patronymic
    
    @admin.display(description='Телефон')
    def telephone(self, obj):
        return obj.user_profile.telephone
    
    @admin.display(boolean = True, description='Организатор')
    def org_status(self, obj):
        return obj.user_profile.org_status
    
class ImageForSpacesAdmin(admin.ModelAdmin):
    list_display = ('space_id', 'image', 'image_tag', 'cover')
    list_filter = ('space_id', 'cover',)
    raw_id_fields = ('space_id',)
    search_fields = ['space_id__name',]
    
    @admin.display(description='Превью')
    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="%s" style="width: 45px; height:45px; object-fit:cover" />' % obj.image.url)
        else:
            return 'Нет изображения'

class ImageForSpacesInline(admin.TabularInline): 
    model = ImageForSpaces
    extra = 0

class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'get_items', 'building_id', 'room_number', 'is_visiable')
    list_filter = ('building_id', 'is_visiable',)
    inlines = [ImageForSpacesInline,]
    filter_horizontal = ('items_id',)
    raw_id_fields = ('building_id',)
    search_fields = ['name', 'description', 'building_id__city', 'building_id__street', 'items_id__name', 'capacity']
    
    @admin.display(description='Особенности')
    def get_items(self, obj):
        return [item.name for item in obj.items_id.all()]

class BuildingAdmin(admin.ModelAdmin):
    list_display = ('city', 'street', 'house')
    list_filter = ('city', 'street')
    list_display_links = ('city', 'street')
    search_fields = ['city', 'street']

class ItemInSpaceAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SpacesReviewAdmin(admin.ModelAdmin):
    list_display = ('review', 'space_id', 'user_id', 'add_date', 'is_visiable')
    list_filter = ('space_id', 'user_id', 'is_visiable')
    date_hierarchy = 'add_date'
    # readonly_fields = ('review', 'space_id', 'user_id')
    search_fields = ['review', 'space_id__name', 'user_id__username', 'add_date', 'user_id__first_name', 'user_id__last_name']

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'space_id', 'date_from', 'date_to', 'status')
    list_filter = ('user_id', 'space_id', 'status')
    date_hierarchy = 'date_from'
    list_display_links = ('user_id', 'space_id')
    # readonly_fields = ('user_id', 'space_id', 'date_to', 'date_from') 
    search_fields = ['user_id__username', 'space_id__name', 'date_from', 'date_to', 'user_id__first_name', 'user_id__last_name']
    
class ImgageForEventsAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'image', 'image_tag', 'cover')
    list_filter = ('event_id', 'cover',)
    raw_id_fields = ('event_id',)
    search_fields = ['event_id__name']
    
    @admin.display(description='Превью')
    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="%s" style="width: 45px; height:45px; object-fit:cover" />' % obj.image.url)
        else:
            return 'Нет изображения'
    
class ImageForEventsInline(admin.TabularInline): 
    model = ImageForEvents
    extra = 0
    
class EventWithItemsInline(admin.TabularInline):
    model = EventWithItems
    extra = 1
    
@admin.action(description="Создать копию")
def duplicate_event(modeladmin, request, queryset):
    for event in queryset:
        event.pk = None 
        event.date += timedelta(weeks=1)
        event.is_visiable = False
        event.save()

@admin.action(description="Сделать неактивными")
def deactivate_events(modeladmin, request, queryset):
    queryset.update(is_visiable=False)
    
@admin.action(description="Перенести на день")
def plus_day(modeladmin, request, queryset):
    for event in queryset:
        Event.objects.filter(id=event.id).update(date=event.date + timedelta(days=1))

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'get_items', 'space_id', 'org_id', 'attachment', 'is_visiable', 'pdf_link')
    list_filter = ('org_id', 'space_id', 'is_visiable',)
    inlines = [ImageForEventsInline, EventWithItemsInline,]
    date_hierarchy = 'date'
    raw_id_fields = ('space_id', 'org_id')
    search_fields = ['name', 'description', 'date', 'space_id__name', 'org_id__name', 'items_id__name']
    actions = [duplicate_event, deactivate_events, plus_day]
    
    @admin.display(description='Особенности')
    def get_items(self, obj):
        return [item.name for item in obj.items_id.all()]
    
    @admin.display(description='PDF-сводка')
    def pdf_link(self, obj):
        url = reverse('event-pdf', args=[obj.pk])
        return format_html(f'<a href="{url}" target="_blank">PDF</a>')
    
@admin.action(description="Проверить мероприятия")
def check_org_events(modeladmin, request, queryset):
    for org in queryset:
        if org.org_events.exists():
            messages.warning(request, f"{org.name} — есть мероприятия")
        else:
            messages.info(request, f"{org.name} — мероприятий нет")

class OrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'charter', 'org_id')
    list_filter = ('org_id',)
    raw_id_fields = ('org_id',)
    search_fields = ['name', 'description', 'org_id__username', 'org_id__first_name', 'org_id__last_name']
    actions = [check_org_events]

class ItemInEventsAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.action(description="Удалить отмененные")
def delete_canceled(modeladmin, request, queryset):
    Registration.objects.filter(Q(status='CBC') | Q(status='CAC')).delete()

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'event_id', 'status')
    list_filter = ('user_id', 'event_id', 'status')
    date_hierarchy = 'reg_date'
    list_display_links = ('user_id', 'event_id')
    # readonly_fields = ('user_id', 'event_id')
    search_fields = ['user_id__username', 'event_id__name']
    actions = [delete_canceled]

class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'event_id', 'space_id', 'add_date')
    list_filter = ('user_id', 'event_id', 'space_id')
    date_hierarchy = 'add_date'
    # readonly_fields = ('user_id', 'event_id', 'space_id')
    search_fields = ['user_id__username', 'user_id__first_name', 'user_id__last_name', 'event_id__name', 'space_id__name', 'add_date']

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Space, SpaceAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(ItemInSpaces, ItemInSpaceAdmin)
admin.site.register(ImageForSpaces, ImageForSpacesAdmin)
admin.site.register(SpacesReview, SpacesReviewAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Organizer, OrganizerAdmin)
admin.site.register(ItemInEvents, ItemInEventsAdmin)
admin.site.register(ImageForEvents, ImgageForEventsAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(Favourite, FavouriteAdmin)
