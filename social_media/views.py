import social_media.serializers as serializer
from social_media.models import Profile, Post, Like

from rest_framework import viewsets, status
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request


from typing import Type


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for the Profile model."""

    queryset = Profile.objects.all()

    @action(list=True, methods=["get"])
    def followers(self, request: Request, pk=None):
        user = self.get_object()
        qs = Profile.objects.filter(target=user)
        serializer = serializer.ProfileFollowsSerializer(qs, many=True)
        return Response(serializer.data)

    @action(list=True, methods=["get"])
    def following(self, request, pk=None):
        user = self.get_object()
        qs = Profile.objects.filter(user=user)
        serializer = serializer.ProfileFollowersSerializer(qs, many=True)
        return Response(serializer.data)

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return serializer.ProfileListSerializer

        if self.action == "retrieve":
            return serializer.ProfileSerializer

        if self.action == "followers":
            return serializer.ProfileFollowsSerializer

        if self.action == "following":
            return serializer.ProfileFollowersSerializer

        return super().get_serializer_class()


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for the Post model."""

    queryset = Post.objects.select_related("user")
    serializer_class = serializer.PostSerializer

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return serializer.PostListSerializer

        if self.action == "retrieve":
            return serializer.PostSerializer

        return super().get_serializer_class()


class LikeViewSet(viewsets.ModelViewSet):
    """ViewSet for the Like model."""

    queryset = Like.objects.select_related("user", "post")
    serializer_class = serializer.LikeSerializer

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return serializer.LikeListSerializer

        if self.action == "retrieve":
            return serializer.LikeDetailSerializer

        return super().get_serializer_class()
