from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import *
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken 

class BookingModelTest(APITestCase):
    def setUp(self) -> None:
        """
        Инициализация тестовых данных:
        - создание тестового пользователя и получение JWT токена
        - создание здания и помещения
        - подготовка URL для бронирования и комментариев
        """
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token) 
        
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {access_token}')        
        
        self.building = Building.objects.create(city="Test City 1", street="Test Street 1", house="1")
        self.space = Space.objects.create(name="Test Space", capacity=10, building_id=self.building, is_visiable=True)
        
        self.booking_url = f'/api/spaces/{self.space.pk}/book/'
        self.comment_url = f'/api/spaces/{self.space.pk}/add_comment/'

    def test_booking_invalid_dates(self) -> None:
        """
        Тест валидации бронирования с некорректными датами (date_to раньше date_from)
        """
        date_from = timezone.now()
        date_to = date_from - timedelta(hours=1)
        booking = Booking.objects.create(user_id=self.user, space_id=self.space, date_from=date_from, date_to=date_to)
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_booking_valid_dates(self) -> None:
        """
        Тест создания бронирования с корректными датами
        Проверяет, что пользователь и помещение совпадают с заданными
        """
        date_from = timezone.now()
        date_to = date_from + timedelta(hours=2)
        booking = Booking.objects.create(user_id=self.user, space_id=self.space, date_from=date_from, date_to=date_to)
        self.assertEqual(booking.user_id, self.user)
        self.assertEqual(booking.space_id, self.space)


class BookingAPITest(APITestCase):
    def setUp(self) -> None:
        """
        Инициализация данных для API тестов:
        - создание пользователя, получение JWT токена
        - создание здания и помещения
        - подготовка URL для бронирования и комментариев
        """
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='pass123')
        
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token) 
        
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {access_token}')
            
        self.building = Building.objects.create(city="Test City 2", street="Test Street 2", house="2")
        self.space = Space.objects.create(name="Room 1", capacity=5, building_id=self.building, is_visiable=True)
        self.booking_url = f'/api/spaces/{self.space.pk}/book/'
        self.comment_url = f'/api/spaces/{self.space.pk}/add_comment/'

    def test_successful_booking(self) -> None:
        """
        Тест успешного бронирования через API
        Проверяет статус ответа 201 CREATED
        """
        date_from = timezone.now() + timedelta(days=1)
        date_to = date_from + timedelta(hours=2)
        response = self.client.post(self.booking_url, {
            "space_id": self.space,
            "date_from": date_from.strftime('%Y-%m-%d %H:%M'),
            "date_to": date_to.strftime('%Y-%m-%d %H:%M')
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_conflicting_booking(self) -> None:
        """
        Тест бронирования в период, когда помещение уже занято
        Ожидает ошибку 400 и сообщение об занятости помещения
        """
        date_from = timezone.now() + timedelta(days=2)
        date_to = date_from + timedelta(hours=2)
        Booking.objects.create(user_id=self.user, space_id=self.space, date_from=date_from, date_to=date_to, status=Booking.Status.CONFIRMATION)
        response = self.client.post(self.booking_url, {
            "space_id": self.space,
            "date_from": date_from.strftime('%Y-%m-%d %H:%M'),
            "date_to": date_to.strftime('%Y-%m-%d %H:%M')
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("помещение занято в выбранный период", response.data.get("error", "").lower())

    def test_filter_by_capacity(self) -> None:
        """
        Тест фильтрации помещений по минимальной вместимости через API
        Проверяет успешный ответ и наличие данных
        """
        response = self.client.get('/api/spaces/', {'min_capacity': 3})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_filter_by_date_and_city(self) -> None:
        """
        Тест фильтрации помещений по дате и городу через API
        Проверяет успешный ответ
        """
        date_from = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
        date_to = (timezone.now() + timedelta(days=3, hours=2)).strftime('%Y-%m-%d %H:%M')
        response = self.client.get('/api/spaces/', {
            'date_from': date_from,
            'date_to': date_to,
            'city': 'Test City 2'
        })
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_booking(self) -> None:
        """
        Тест попытки бронирования без авторизации
        Ожидается ответ 401 Unauthorized
        """
        self.client.logout()
        date_from = timezone.now() + timedelta(days=1)
        date_to = date_from + timedelta(hours=2)
        response = self.client.post(self.booking_url, {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_comment_without_booking(self) -> None:
        """
        Тест добавления комментария без наличия бронирования
        Ожидается отказ с кодом 403 Forbidden
        """
        response = self.client.post(self.comment_url, {"review": "test"})
        self.assertEqual(response.status_code, 403)

    def test_add_comment_with_booking(self) -> None:
        """
        Тест добавления комментария при наличии подтвержденного бронирования
        Ожидается успешное создание комментария с кодом 201 Created
        """
        date_from = timezone.now() - timedelta(days=2)
        date_to = timezone.now() - timedelta(days=1)
        Booking.objects.create(user_id=self.user, space_id=self.space, date_from=date_from, date_to=date_to, status=Booking.Status.CONFIRMATION)
        response = self.client.post(self.comment_url, {"review": "test"})
        self.assertEqual(response.status_code, 201)

    def test_get_user_profile(self) -> None:
        """
        Тест получения профиля текущего пользователя через API
        Проверяет, что возвращается корректный username
        """
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'apiuser')

