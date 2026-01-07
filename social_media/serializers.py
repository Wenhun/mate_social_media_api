from rest_framework import serializers
from django.contrib.auth import get_user_model
from social_media.models import Profile, Post, Like


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


class PostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "user", "text", "created_at", "updated_at", "image")


class PostListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "user", "text", "updated_at")


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "image")


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("id", "user", "post", "created_at", "updated_at")


class LikeDetailSerializer(LikeSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    post = PostSerializer(read_only=True, many=False)


class LikeListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    post_by = serializers.CharField(source="post.user.username", read_only=True)
    post_text = serializers.CharField(source="post.text", read_only=True)

    class Meta:
        model = Like
        fields = ("id", "user", "post_by", "post_text", "updated_at")


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)
