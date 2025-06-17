from django.db import models
from django.contrib.auth.models import *
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError


# Пользовательская информация  
class Profile(models.Model):
    """
    Дополнительная информация о пользователе
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name='user_profile')
    patronymic = models.CharField(max_length=255, blank=True, verbose_name="Отчество")
    telephone = models.CharField(max_length=12, verbose_name="Телефон")
    image = models.ImageField(blank=True, default=None, upload_to='users/', verbose_name="Аватар")
    telegram_link = models.URLField("Профиль в Telegram", blank=True, null=True)
    org_status = models.BooleanField(default=False, verbose_name="Организатор")
    admin_status = models.BooleanField(default=False, verbose_name="Администратор")
    
    class Meta:
        verbose_name = "Дополнительная информация о пользователях"
        verbose_name_plural = 'Дополнительная информация о пользователях'
        
    def __str__(self) -> str:
        return self.user.first_name + ' ' + self.user.last_name + ' ' + self.patronymic

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs) -> None:
    """
    Создание профиля при регистрации нового пользователя
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs) -> None:
    """
    Сохранение профиля пользователя при обновлении
    """
    instance.user_profile.save()

# Информация о помещениях   
class Building(models.Model):
    """
    Модель здания
    """
    city = models.CharField(max_length=255, verbose_name="Город")
    street = models.CharField(max_length=255, verbose_name="Улица")
    house = models.CharField(max_length=255, verbose_name="Дом")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Здания"
        verbose_name_plural = 'Здания'
    
    def __str__(self) -> str:
        return self.city + ', ' + self.street + ', ' + self.house 
    
class ItemInSpaces(models.Model):
    """
    Особенности помещений (например, проектор, доска)
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Особенности помещений"
        verbose_name_plural = 'Особенности помещений'
    
    def __str__(self) -> str:
        return self.name 
    
class VisiableManager(models.Manager):
    """
    Менеджер, возвращающий только видимые помещения
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_visiable=True)
 
class Space(models.Model):
    """
    Модель помещения
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.CharField(max_length=255, verbose_name="Описание")
    capacity = models.IntegerField(default=0, verbose_name="Вместимость")
    items_id = models.ManyToManyField(ItemInSpaces, verbose_name="Особенности")
    building_id = models.ForeignKey(Building, on_delete=models.PROTECT, verbose_name="Здание")
    room_number = models.CharField(max_length=12, verbose_name="Номер помещения")
    add_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    is_visiable = models.BooleanField(default=False, verbose_name="Показывать")
    
    objects = models.Manager()
    check_visiable = VisiableManager() 
    
    class Meta:
        verbose_name = "Помещения"
        verbose_name_plural = 'Помещения'
    
    def __str__(self) -> str:
        return self.name 
    
    def get_absolute_url(self) -> str:
        return reverse('bron:space-detail', args=[self.id])
    
class ImageForSpaces(models.Model):
    """
    Изображения, прикреплённые к помещениям
    """
    image = models.ImageField(null=True, default=None, upload_to='spaces/', verbose_name="Изображение")
    space_id = models.ForeignKey(Space, on_delete=models.CASCADE, verbose_name="Помещение", related_name="space_images")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")   
    cover = models.BooleanField(default=False, verbose_name="Обложка")
    
    class Meta:
        verbose_name = "Изображения помещений"
        verbose_name_plural = 'Изображения помещений'
    
    def __str__(self) -> str:
        return self.space_id.name
    
class SpacesReview(models.Model):
    """
    Отзывы о помещениях от пользователей
    """
    review = models.CharField(max_length=1023, verbose_name="Отзыв")
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    space_id = models.ForeignKey(Space, on_delete=models.CASCADE, verbose_name="Помещение", related_name="space_reviews")
    add_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")   
    is_visiable = models.BooleanField(default=True, verbose_name="Показывать")    
    
    class Meta:
        verbose_name = "Отзывы на помещения"
        verbose_name_plural = 'Отзывы на помещения'
        ordering = ['-add_date']
        
    def __str__(self) -> str:
        return 'От ' + self.user_id.first_name + ' ' + self.user_id.last_name + ' на ' + self.space_id.name
    
class Booking(models.Model):
    """
    Модель бронирования помещения
    """
    class Status(models.TextChoices):
        NEWBOOK = 'NB', 'Новая бронь'
        CANCELEDBEFORECONFIRMATION = 'CBC', 'Отмена ДО подтверждения'
        CONFIRMATION = 'C', 'Подтверждена'
        CANCELAFTERCONFIRMATION = 'CAC', 'Отмена ПОСЛЕ подтверждения'
    
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="user_books")
    space_id = models.ForeignKey(Space, on_delete=models.CASCADE, verbose_name="Помещение", related_name="space_books")
    date_from = models.DateTimeField(default=timezone.now, verbose_name="Дата начала брони")   
    date_to = models.DateTimeField(default=timezone.now, verbose_name="Дата конца брони")   
    book_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата брони")    
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.NEWBOOK, verbose_name="Статус")
    
    class Meta:
        verbose_name = "Бронирования"
        verbose_name_plural = 'Бронирования'
        ordering = ['-book_date']
    
    def __str__(self) -> str:
        return self.space_id.name + ' на ' + self.date_from.strftime("%d.%m.%Y") + '-' + self.date_to.strftime("%d.%m.%Y") + ' для ' + self.user_id.first_name + ' ' + self.user_id.last_name
    
    def clean(self) -> None:
        """
        Валидация: дата начала должна быть раньше даты окончания
        """
        if self.date_from >= self.date_to:
            raise ValidationError("Дата начала должна быть раньше даты окончания") 

# Информация о мероприятиях   
class Organizer(models.Model):
    """
    Модель организатора мероприятия
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    org_id = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Руководитель", related_name='user_organizers')
    charter = models.FileField(upload_to='orgs/docs', null=True, blank=True, verbose_name="Устав")
    add_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Организаторы"
        verbose_name_plural = 'Организаторы'
    
    def __str__(self) -> str:
        return self.name 
    
    def get_absolute_url(self) -> str:
        return reverse('bron:organizer-detail', args=[self.id])
    
class ItemInEvents(models.Model):
    """
    Особенности мероприятий (например, еда, техника)
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Особенности мероприятий"
        verbose_name_plural = 'Особенности мероприятий'
    
    def __str__(self) -> str:
        return self.name 
    
class Event(models.Model):
    """
    Модель мероприятия
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата проведения")
    items_id = models.ManyToManyField(ItemInEvents, blank=True, through='EventWithItems', through_fields=('event', 'item'), verbose_name="Особенности")
    space_id = models.ForeignKey(Space, on_delete=models.PROTECT, blank=True, verbose_name="Помещение", related_name="space_events")
    org_id = models.ForeignKey(Organizer, on_delete=models.PROTECT, verbose_name="Организатор", related_name="org_events")
    attachment = models.FileField(upload_to='events/docs', null=True, blank=True, verbose_name="Приложение")
    add_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    is_visiable = models.BooleanField(default=True, verbose_name="Показывать")    
    
    class Meta:
        verbose_name = "Мероприятия"
        verbose_name_plural = 'Мероприятия'
        ordering = ['date']
        
    def __str__(self) -> str:
        return self.name + ' (' + str(self.date.strftime("%d.%m.%Y")) + ')'
    
    def get_absolute_url(self) -> str:
        return reverse('bron:event-detail', args=[self.id])
    
class EventWithItems(models.Model):
    """
    Промежуточная модель между Event и ItemInEvents
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятия")
    item = models.ForeignKey(ItemInEvents, on_delete=models.CASCADE, verbose_name="Особенность")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Мероприятия и особенности"
        verbose_name_plural = 'Мероприятия и особенности'
    
    def __str__(self) -> str:
        return self.event.name + self.item.name 

class ImageForEvents(models.Model):
    """
    Изображения мероприятий
    """
    image = models.ImageField(null=True, default=None, upload_to='events/', verbose_name="Изображение")
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие", related_name="event_images")
    add_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")   
    cover = models.BooleanField(default=False, verbose_name="Обложка") 
    
    class Meta:
        verbose_name = "Изображения мероприятий"
        verbose_name_plural = 'Изображения мероприятий'
        
    def __str__(self) -> str:
        return self.event_id.name + ' (' + str(self.event_id.date.strftime("%d.%m.%Y")) + ')'

class Registration(models.Model):
    """
    Регистрация пользователя на мероприятие
    """
    class Status(models.TextChoices):
        NEWREG = 'NR', 'Новая регистрация'
        CANCELEDBEFORECONFIRMATION = 'CBC', 'Отмена ДО подтверждения'
        CONFIRMATION = 'C', 'Подтверждена'
        CANCELAFTERCONFIRMATION = 'CAC', 'Отмена ПОСЛЕ подтверждения'

    user_id = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="user_regs")
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие", related_name="event_regs")
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")    
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.NEWREG, verbose_name="Статус") 

    class Meta:
        verbose_name = "Регистрации"
        verbose_name_plural = 'Регистрации'
        ordering = ['-reg_date']
        
    def __str__(self) -> str:
        return self.user_id.first_name + ' ' + self.user_id.last_name + ' на ' + self.event_id.name + ' (' + str(self.event_id.date.strftime("%d.%m.%Y")) + ')'

# Избранное
class Favourite(models.Model):
    """
    Избранные мероприятия и помещения пользователя
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="user_fav")
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True, default=None, verbose_name="Мероприятие", related_name="fav_event")
    space_id = models.ForeignKey(Space, on_delete=models.CASCADE, blank=True, null=True, default=None, verbose_name="Помещение", related_name='favourite')
    add_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")   
    
    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = 'Избранное'
        ordering = ['-add_date']
    
    def __str__(self) -> str:
        return self.user_id.first_name + ' ' + self.user_id.last_name 
