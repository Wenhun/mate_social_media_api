import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def get_file_path(instance: models.Model, filename: str) -> str:
    """
    Module-level callable so migrations can import social_media.models.get_file_path.
    Chooses upload subdir based on the model class name to match previous behavior.
    """
    _, extension = os.path.splitext(filename)
    model_name = instance.__class__.__name__.lower()
    dir_map = {"profile": "profile", "post": "posts"}
    upload_dir = dir_map.get(model_name, model_name)
    filename = f"{slugify(instance.pk)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads", upload_dir, filename)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    follows = models.ManyToManyField(
        "self", related_name="followed_by", symmetrical=False, blank=True
    )
    image = models.ImageField(null=True, blank=True, upload_to=get_file_path)

    def __str__(self) -> str:
        return f"Profile (id: {self.pk}) by {self.user.username}"


@receiver(post_save, sender=User)
def create_profile(
    sender: User, instance: User, created: bool, *args, **kwargs
) -> None:
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        user_profile.follows.set([instance.profile.pk])  # type: ignore
        user_profile.save()


class ContentBase(models.Model):
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(null=True, blank=True, upload_to=get_file_path)

    class Meta:
        abstract = True


class Post(ContentBase):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")

    def __str__(self) -> str:
        return f"Post (id: {self.pk}) by {self.user.username}: {self.text}"


class Comment(ContentBase):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")

    def __str__(self) -> str:
        return f"Comment (id: {self.pk}) by {self.user.username} to post {self.post.pk}: {self.text}"


class PostLike(models.Model):
    class Meta:  # type: ignore
        unique_together = ("user", "post")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Post (id: {self.post.pk}) is liked by {self.user.username}"


class CommentLike(models.Model):
    class Meta:  # type: ignore
        unique_together = ("user", "comment")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_likes"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="comment_likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comment (id: {self.comment.pk}) is liked by {self.user.username}"
