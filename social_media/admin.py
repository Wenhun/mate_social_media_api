from django.contrib import admin

from social_media.models import (
    Profile,
    Post,
    Comment,
    PostLike,
    CommentLike,
    ScheduledPost,
)

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostLike)
admin.site.register(CommentLike)
admin.site.register(ScheduledPost)
