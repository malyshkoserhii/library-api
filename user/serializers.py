from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "style": {"input_type": "password"},
                "label": _("Password"),
                "min_length": 5,  # опціонально, але гарна практика
            }
        }

    def create(self, validated_data):
        """Create user with encrypted password"""
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update User with encrypted password"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user
