from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import UserViewSet, EventViewSet, SpaceViewSet, BookingViewSet, UserCurrentViewSet, OrganizerViewSet, WidgetViewSet

app_name = "bron"

router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register('events', EventViewSet)
router.register('spaces', SpaceViewSet)
router.register('bookings', BookingViewSet)
router.register('orgs', OrganizerViewSet)
router.register('widgets', WidgetViewSet, basename='widgets')

urlpatterns = router.urls + [
    path('me/', UserCurrentViewSet.as_view(), name='user-profile'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/jwt/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
]