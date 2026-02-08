from social_media.serializers import *
from user.serializers import UserSerializer
from social_media.models import CommentLike, Profile, Post, PostLike

from django.db.models.query import QuerySet
from rest_framework import viewsets, status
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from django.db.models import Q

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse  # type: ignore

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
        if self.action == "update":
            return ProfileUpdateSerializer

        return super().get_serializer_class()

    def _serialize_profile(self, request: Request) -> Type[Response]:
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: ProfileFollowersSerializer,
        },
        methods=["GET"],
        description="Provides a list of users who follow the authorized user",
    )
    @action(methods=["GET"], detail=True, url_path="followers")
    def followers(self, request: Request, pk: int = None) -> Type[Response]:  # type: ignore
        return self._serialize_profile(request)

    @extend_schema(
        responses={
            200: ProfileFollowsSerializer,
        },
        methods=["GET"],
        description="Provides a list of users that the authorized user is following",
    )
    @action(methods=["GET"], detail=True, url_path="following")
    def following(self, request: Request, pk: int = None) -> Type[Response]:  # type: ignore
        return self._serialize_profile(request)

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(description="Add user to follow"),
            204: OpenApiResponse(description="Remove user from follow"),
        },
        methods=["POST"],
        description="Toggle follow user. User ID is automatically added for authorized users",
    )
    @action(methods=["POST"], detail=True)
    def follow_profile_toggle(self, request: Request, pk: int = None) -> Response:  # type: ignore
        user_profile = request.user.profile
        target_profile = self.get_object()

        if user_profile == target_profile:
            return Response(
                {"detail": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_following = target_profile.followed_by.filter(pk=user_profile.pk).exists()

        if is_following:

            target_profile.followed_by.remove(user_profile)
            return Response(status=status.HTTP_204_NO_CONTENT)

        target_profile.followed_by.add(user_profile)
        return Response({"detail": "Followed"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={
            204: ProfileDetailSerializer,
        },
        methods=["DELETE"],
        description="Delete profile and linked user",
    )
    def destroy(self, request: Request, *args, **kwargs) -> Type[Response]:  # type: ignore
        """Function delete User with Cascade deleting Profile"""

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "username",
                type=OpenApiTypes.STR,
                description="Filter by username (ex. ?username='bob')",
            ),
        ]
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)


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

        if self.action == "upload_image":
            return PostImageSerializer

        if self.action == "user_posts":
            return PostUserListSerializer

        if self.action == "posts_from_follows":
            return PostListSerializer

        if self.action == "show_user_draft_posts":
            return PostListSerializer

        if self.action == "show_user_scheduled_posts":
            return PostListSerializer

        return super().get_serializer_class()

    def get_queryset(self) -> QuerySet[Post]:
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return self.queryset

        hashtag = self.request.query_params.get("hashtag")  # type: ignore

        queryset = self.queryset.filter(
            Q(schedule_post__isnull=True)
            | Q(schedule_post__status=ScheduledPost.StatusChoices.PUBLISHED)
        )

        if hashtag:
            queryset = queryset.filter(text__regex=rf"(^|\s)#{hashtag}(?=\s|$)")

        return queryset.distinct()

    @extend_schema(
        responses={200: PostListSerializer, 204: None},
        methods=["GET"],
        description="Showing posts with status 'Draft' by authorized user",
    )
    @action(methods=["GET"], detail=False, url_path="drafts")
    def show_user_draft_posts(self, request: Request, pk: int = None) -> Type[Response]:
        user = self.request.user
        queryset = self.queryset.filter(user=user)
        queryset = queryset.filter(
            schedule_post__isnull=False,
            schedule_post__status=ScheduledPost.StatusChoices.DRAFT,
        )

        if queryset:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "No post with status 'Draft'."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        responses={200: PostListSerializer, 204: None},
        methods=["GET"],
        description="Showing posts with status 'Scheduled' by authorized user",
    )
    @action(methods=["GET"], detail=False, url_path="scheduled")
    def show_user_scheduled_posts(
        self, request: Request, pk: int = None
    ) -> Type[Response]:
        user = self.request.user
        queryset = self.queryset.filter(user=user)
        queryset = queryset.filter(
            schedule_post__isnull=False,
            schedule_post__status=ScheduledPost.StatusChoices.SCHEDULED,
        )

        if queryset:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "No post with status 'Scheduled'."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        responses={200: PostUserListSerializer, 204: None},
        methods=["GET"],
        description="Showing posts by authorized user",
    )
    @action(methods=["GET"], detail=False, url_path="my_posts")
    def user_posts(self, request: Request, pk: int = None) -> Type[Response]:  # type: ignore
        user = self.request.user
        queryset = self.queryset.filter(user=user)
        if queryset:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "The user has not created any posts yet."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        responses={
            200: PostListSerializer,
        },
        methods=["GET"],
        description="Shows posts followed by the authorized user",
    )
    @action(methods=["GET"], detail=False, url_path="posts_from_follows")
    def posts_from_follows(self, request: Request, pk: int = None) -> Type[Response]:  # type: ignore
        if request.user.is_authenticated:
            profile = Profile.objects.get(user=request.user)
            following_user_ids = profile.follows.values_list("user_id", flat=True)
            posts = self.queryset.filter(user_id__in=following_user_ids)
            serializer = self.get_serializer(posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED
        )  # type: ignore

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(description="Create like on post"),
            204: OpenApiResponse(description="Remove like from post"),
        },
        methods=["POST"],
        description="Toggle like on post. User ID is automatically added for authorized users",
    )
    @action(methods=["POST"], detail=True)
    def like_toggle(self, request: Request, pk: int = None) -> Response:  # type: ignore
        user = request.user
        post = self.get_object()

        post_like = PostLike.objects.filter(post=post, user=user).first()

        if post_like:
            post_like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        PostLike.objects.create(post=post, user=user)
        return Response({"detail": "Like added"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={
            201: PostSerializer,
        },
        methods=["POST"],
        description="Create post. User ID is automatically added",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "hashtag",
                type=OpenApiTypes.STR,
                description="Filter by hashtag (ex. ?hashtag='#bob'). Symbol '#' is added automatically",
            ),
        ]
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet, UploadImageMixin):
    queryset = Comment.objects.select_related("post", "user")
    serializer_class = CommentSerializer

    def get_serializer_class(self) -> Type[ModelSerializer]:  # type: ignore
        """Return the appropriate serializer class based on the request."""

        if self.action == "list":
            return CommentsListSerializer

        if self.action == "retrieve":
            return CommentsDetailSerializer

        if self.action == "upload_image":
            return CommentImageSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer: ModelSerializer) -> None:
        serializer.save(user=self.request.user, post_id=self.kwargs["post_pk"])

    @extend_schema(
        responses={
            201: CommentSerializer,
        },
        methods=["POST"],
        description="Create comment. User ID and Post ID is automatically added for authorized users",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Comment]:  # type: ignore
        return Comment.objects.select_related("post", "user").filter(
            post_id=self.kwargs["post_pk"]
        )

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(description="Create like on comment"),
            204: OpenApiResponse(description="Remove like from comment"),
        },
        methods=["POST"],
        description="Toggle like on comment. User ID and Post ID is automatically added for authorized users and parent post",
    )
    @action(methods=["POST"], detail=True)
    def like_toggle(self, request: Request, post_pk: int = None, pk: int = None) -> Response:  # type: ignore
        user = request.user
        comment = self.get_object()

        comment_like = CommentLike.objects.filter(comment=comment, user=user).first()

        if comment_like:
            comment_like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        CommentLike.objects.create(comment=comment, user=user)
        return Response({"detail": "Like added"}, status=status.HTTP_201_CREATED)
