from urllib import request
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from social_media.models import Profile, Post, Comment, ScheduledPost
from django.utils import timezone

from .tasks import publish_post_task


class ProfileListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "user")


class ProfileFollowsSerializer(serializers.ModelSerializer):
    follows = ProfileListSerializer(read_only=True, many=True)

    class Meta:
        model = Profile
        fields = ("id", "follows")


class ProfileFollowersSerializer(serializers.ModelSerializer):
    followers = ProfileListSerializer(source="followed_by", many=True)

    class Meta:
        model = Profile
        fields = ("id", "followers")


class ProfileDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    follows = ProfileListSerializer(read_only=True, many=True)
    following = ProfileListSerializer(source="followed_by", many=True)

    class Meta:
        model = Profile
        fields = ("id", "user", "bio", "follows", "following", "image")


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "image")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "bio", "image")


class PostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    likes_by = serializers.SerializerMethodField()
    count_likes = serializers.IntegerField(source="post_likes.count", read_only=True)
    count_comments = serializers.IntegerField(source="comments.count", read_only=True)
    time_to_publishing = serializers.DateTimeField(required=False, allow_null=True)
    post_status = serializers.ChoiceField(
        choices=ScheduledPost.StatusChoices, request=False, allow_null=True
    )

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "text",
            "created_at",
            "updated_at",
            "likes_by",
            "image",
            "count_likes",
            "count_comments",
            "time_to_publishing",
            "post_status",
        )

    def get_likes_by(self, obj) -> list:
        return [like.user.username for like in obj.post_likes.all()]

    def create(self, validated_data: dict) -> Post:
        time = validated_data.pop("time_to_publishing", None)
        status = validated_data.pop("post_status", None)
        user = self.context["request"].user
        post = Post.objects.create(user=user, **validated_data)

        if not time:
            return post

        if time <= timezone.now():
            return post

        scheduled = ScheduledPost.objects.create(
            post=post, time=time, status=status or ScheduledPost.StatusChoices.DRAFT
        )

        if scheduled.status == ScheduledPost.StatusChoices.SCHEDULED:

            publish_post_task.apply_async(args=[scheduled.pk], eta=scheduled.time)  # type: ignore

        return post


class PostListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    count_likes = serializers.IntegerField(source="post_likes.count", read_only=True)
    count_comments = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "user", "text", "updated_at", "count_comments", "count_likes")


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "image")


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: dict) -> User:
        return get_user_model().objects.create_user(**validated_data)  # type: ignore


class PostCommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "user", "text")


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "text", "image")


class CommentsDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    post = PostCommentSerializer(read_only=True, many=False)
    likes_by = serializers.SerializerMethodField()
    count_likes = serializers.IntegerField(source="comment_likes.count", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "post",
            "text",
            "created_at",
            "updated_at",
            "likes_by",
            "count_likes",
            "image",
        )

    def get_likes_by(self, obj) -> list:
        return [like.user.username for like in obj.comment_likes.all()]


class CommentsListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    count_likes = serializers.IntegerField(source="comment_likes.count", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "text", "count_likes")


class CommentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "image")
