from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import *

app_name = "bron"

router = routers.DefaultRouter()
router.register('adminusers', UserMakeAdminViewSet, basename='users-makeadmin')
router.register('events', EventViewSet)
router.register(r'spaces', SpaceViewSet, basename='space')
router.register('spaceshidden', SpaceHiddenViewSet, basename='spacehidden')
router.register('bookings', BookingViewSet)
router.register('newbookings', NewBookingViewSet, basename='newbookings')
router.register('orgs', OrganizerViewSet)
router.register('widgets', WidgetViewSet, basename='widgets')
router.register('buildings', BuildingViewSet)
router.register('itemsinspace', ItemsInSpacesViewSet)
router.register('mvexam', ExamViewSet)

urlpatterns = router.urls + [
    path('me/', UserCurrentViewSet.as_view(), name='user-profile'),
    path('users/', UserAdminViewSet.as_view(), name='users'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/jwt/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
]