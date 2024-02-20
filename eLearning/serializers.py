from rest_framework import serializers
from .models import User, Course


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["photo"]

    def validate_photo(self, value):
        """
        Check if the uploaded file is an image.
        """
        if value:
            if not value.content_type.startswith("image"):
                raise serializers.ValidationError("Only image files are allowed.")
        return value

    def update(self, instance, validated_data):
        """
        Update the user's photo field.
        """
        instance.photo = validated_data.get("photo", instance.photo)
        instance.save()
        return instance
