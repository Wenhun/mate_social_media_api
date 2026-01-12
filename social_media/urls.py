from django.urls import path, include
from rest_framework_nested import routers as nested_routers
from rest_framework import routers

from social_media.views import *

app_name = "social_media"

default_router = routers.DefaultRouter()
default_router.register(r"profiles", ProfileViewSet, basename="profiles")
default_router.register(r"posts", PostViewSet, basename="posts")

posts_router = nested_routers.NestedSimpleRouter(
    default_router, r"posts", lookup="post"
)
posts_router.register(r"comments", CommentViewSet, basename="post-comments")


urlpatterns = default_router.urls + posts_router.urls
