import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


def image_file_path(upload_dir: str):
    def get_file_path(instance: models.Model, filename: str) -> str:
        _, extension = os.path.splitext(filename)
        filename = f"{slugify(instance.pk)}-{uuid.uuid4()}{extension}"
        return os.path.join("uploads", upload_dir, filename)

    return get_file_path


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    follows = models.ManyToManyField(
        "self", related_name="followed_by", symmetrical=False, blank=True
    )
    image = models.ImageField(
        null=True, blank=True, upload_to=image_file_path("profile")
    )

    def __str__(self) -> str:
        return f"Profile (id: {self.pk}) by {self.user.username}"


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(null=True, blank=True, upload_to=image_file_path("posts"))

    def __str__(self) -> str:
        return f"Post (id: {self.pk}) by {self.user.username}: {self.text})"


class Like(models.Model):
    class Meta:
        unique_together = ("user", "post")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Post (id: {self.post.pk}) is liked by {self.user.username}"
