from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from social_media.models import Profile, Post, PostLike, Comment

from typing import Type


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


class CommentsSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "text", "created_at", "updated_at", "post", "image")


class PostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    comments = CommentsSerializer(read_only=True, many=True)
    count_likes = serializers.IntegerField(source="post_likes.count", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "text",
            "created_at",
            "updated_at",
            "comments",
            "image",
            "count_likes",
        )


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


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ("id", "user", "post", "created_at")


class LikeDetailSerializer(LikeSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    post = PostSerializer(read_only=True, many=False)


class LikeListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    post_by = serializers.CharField(source="post.user.username", read_only=True)
    post_text = serializers.CharField(source="post.text", read_only=True)

    class Meta:
        model = PostLike
        fields = ("id", "user", "post_by", "post_text")


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: dict) -> User:
        return get_user_model().objects.create_user(**validated_data)  # type: ignore
