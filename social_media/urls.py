from django.urls import path, include
from rest_framework import routers

from social_media.views import *

app_name = "social_media"

router = routers.DefaultRouter()
router.register(r"profiles", ProfileViewSet, basename="profiles")
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"likes", LikeViewSet, basename="likes")

urlpatterns = [path("", include(router.urls))]
