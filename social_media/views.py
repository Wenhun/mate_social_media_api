from social_media.serializers import *
from social_media.models import Profile, Post, PostLike

from django.db.models.query import QuerySet
from rest_framework.decorators import api_view
from rest_framework import viewsets, status, generics
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth import get_user_model


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

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
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

    def _serialize_profile(self, request: Request) -> Type[Response]:
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="followers")
    def followers(self, request, pk=None) -> Type[Response]:
        return self._serialize_profile(request)

    @action(methods=["GET"], detail=True, url_path="following")
    def following(self, request, pk=None) -> Type[Response]:
        return self._serialize_profile(request)

    def destroy(self, request: Request, *args, **kwargs) -> Type[Response]:  # type: ignore
        """Rewrite function. Function delete User with Cascade deleting Profile"""

        instance = self.get_object()
        self.perform_destroy(get_user_model().objects.get(pk=instance.user.pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self) -> QuerySet[Profile]:  # type: ignore
        """Retrieve the profiles with filters"""
        username = self.request.query_params.get("username")  # type: ignore

        queryset = self.queryset

        if username:
            queryset = queryset.filter(user__username__icontains=username)

        return queryset.distinct()


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

    def get_queryset(self) -> QuerySet[Post]:  # type: ignore
        """Retrieve the profiles with filters"""
        hashtag = self.request.query_params.get("hashtag")  # type: ignore

        queryset = self.queryset

        if hashtag:
            queryset = queryset.filter(text__regex=rf"(^|\s)#{hashtag}(?=\s|$)")

        return queryset.distinct()


class LikeViewSet(viewsets.ModelViewSet):
    """ViewSet for the Like model."""

    queryset = PostLike.objects.select_related("user", "post")
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
