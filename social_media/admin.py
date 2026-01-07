from django.contrib import admin

from social_media.models import Profile, Post, Like

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Like)
