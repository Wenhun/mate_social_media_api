from rest_framework.permissions import BasePermission, SAFE_METHODS

from rest_framework.request import Request
from rest_framework.views import APIView


class CanEditOwnProfileOrAdmin(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: any):
        if request.method in SAFE_METHODS:
            return True

        return True if request.user.is_staff else obj.user == request.user


class UserCannotActOnSelf(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: any):
        return True if request.user.is_staff else obj.user != request.user
