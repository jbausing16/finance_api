from rest_framework import serializers
from core import models as core_model


class AccountSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(source="user_type.id")
    name = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email")
    image = serializers.SerializerMethodField()

    class Meta:
        model = core_model.UserAcc
        fields = ['user_type', 'name', 'email', 'image']

    def get_name(self, obj):
        fname = obj.user.first_name
        lname = obj.user.last_name
        return f"{fname} {lname}"

    def get_image(self, obj):
        if obj.profile:
            return obj.profile.url
        # elif obj.client.logo:
        #     return obj.client.logo.url
        else:
            return ""
