from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core_backend.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)

        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['roles'] = {
            "operator": user.is_operator,
            "provider": user.is_provider,
            "recipient": user.is_recipient,
            "requester": user.is_requester,
            "payer": user.is_payer,
            "admin": user.is_admin,
        }
        token['permissions'] = []  # TODO fetch permissions here

        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirmation = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'confirmation')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmation']:
            raise serializers.ValidationError(
                {"confirmation": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user
