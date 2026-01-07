from social_media.serializers import *
from social_media.models import Profile, Post, Like

from django.db.models.query import QuerySet
from rest_framework.decorators import api_view
from rest_framework import viewsets, status, generics
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request


from typing import Type


class UploadImageMixin:
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request: Request, pk: int = None) -> Response:  # type: ignore
        """Endpoint for uploading an image to a specific object"""

        obj = self.get_object()  # type: ignore
        serializer = self.get_serializer(obj, data=request.data)  # type: ignore

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet, UploadImageMixin):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer

    def get_serializer_class(self):  # type: ignore
        if self.action == "followers":
            return ProfileFollowersSerializer
        if self.action == "following":
            return ProfileFollowsSerializer
        if self.action == "retrieve":
            return ProfileDetailSerializer
        if self.action == "list":
            return ProfileListSerializer
        if self.action == "upload_image":
            return ProfileImageSerializer
        if self.action == "create":
            return UserSerializer

        return super().get_serializer_class()

    def _serialize_profile(self, request):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="followers")
    def followers(self, request, pk=None):
        return self._serialize_profile(request)

    @action(methods=["GET"], detail=True, url_path="following")
    def following(self, request, pk=None):
        return self._serialize_profile(request)


class PostViewSet(viewsets.ModelViewSet, UploadImageMixin):
    """ViewSet for the Post model."""

    queryset = Post.objects.select_related("user")
    serializer_class = PostSerializer

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return PostListSerializer

        if self.action == "retrieve":
            return PostSerializer

        return super().get_serializer_class()


class LikeViewSet(viewsets.ModelViewSet):
    """ViewSet for the Like model."""

    queryset = Like.objects.select_related("user", "post")
    serializer_class = LikeSerializer

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return LikeListSerializer

        if self.action == "retrieve":
            return LikeDetailSerializer

        if self.action == "upload_image":
            return PostImageSerializer

        return super().get_serializer_class()
