from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField(
        "self", related_name="followed_by", symmetrical=False, blank=True
    )

    def __str__(self) -> str:
        return f"Profile (id: {self.pk}) by {self.user.username}"


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    text = models.CharField(max_length=500)
    image = models.ImageField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Post (id: {self.pk}) by {self.user.username}: {self.text})"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    post = models.ForeignKey(Post, on_delete=models.DO_NOTHING)
    is_liked = models.BooleanField(null=True, blank=True)

    def __str__(self) -> str:
        if self.is_liked:
            return f"Post (id: {self.post.pk}) is liked by {self.user.username}"
        else:
            return f"Post (id: {self.post.pk}) is not liked by {self.user.username}"
