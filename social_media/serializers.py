from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from social_media.models import Profile, Post, Comment, ScheduledPost
from django.utils import timezone

from social_media.tasks import publish_post_task


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
    time_to_publishing = serializers.DateTimeField(
        required=False, allow_null=True, write_only=True
    )
    post_status = serializers.ChoiceField(
        choices=ScheduledPost.StatusChoices.choices,
        required=False,
        allow_null=True,
        write_only=True,
    )
    published_at = serializers.DateTimeField(
        source="schedule_post.time", read_only=True
    )
    status = serializers.CharField(source="schedule_post.status", read_only=True)

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
            "published_at",
            "status",
        )

    def get_likes_by(self, obj) -> list:
        return [like.user.username for like in obj.post_likes.all()]

    def create(self, validated_data: dict) -> Post:
        time = validated_data.pop("time_to_publishing", None)
        status = validated_data.pop("post_status", None)
        user = self.context["request"].user

        post = Post.objects.create(user=user, **validated_data)

        if status is None:
            if not time:
                return post

            if time <= timezone.now():
                raise serializers.ValidationError(
                    {"time_to_publishing": "Time must be in the future."}
                )

            ScheduledPost.objects.create(
                post=post, time=time, status=ScheduledPost.StatusChoices.DRAFT
            )
            return post

        if status == ScheduledPost.StatusChoices.DRAFT:
            if not time:
                ScheduledPost.objects.create(
                    post=post, status=ScheduledPost.StatusChoices.DRAFT
                )
                return post

            if time <= timezone.now():
                raise serializers.ValidationError(
                    {"time_to_publishing": "Time must be in the future."}
                )

            ScheduledPost.objects.create(
                post=post, time=time, status=ScheduledPost.StatusChoices.DRAFT
            )
            return post

        if status == ScheduledPost.StatusChoices.SCHEDULED:
            if not time:
                raise serializers.ValidationError(
                    {
                        "time_to_publishing": "Scheduled posts must have a publishing time."
                    }
                )

            if time <= timezone.now():
                raise serializers.ValidationError(
                    {"time_to_publishing": "Time must be in the future."}
                )

            scheduled = ScheduledPost.objects.create(
                post=post, time=time, status=ScheduledPost.StatusChoices.SCHEDULED
            )

            publish_post_task.apply_async(args=[scheduled.id], eta=scheduled.time)
            return post

        return post


class PostListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    count_likes = serializers.IntegerField(source="post_likes.count", read_only=True)
    count_comments = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "user", "text", "updated_at", "count_comments", "count_likes")


class PostUserListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    count_likes = serializers.IntegerField(source="post_likes.count", read_only=True)
    count_comments = serializers.IntegerField(source="comments.count", read_only=True)
    published_at = serializers.DateTimeField(
        source="schedule_post.time", read_only=True
    )
    status = serializers.CharField(source="schedule_post.status", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "text",
            "updated_at",
            "count_comments",
            "count_likes",
            "published_at",
            "status",
        )


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "image")


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
