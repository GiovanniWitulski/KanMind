from rest_framework import generics, status, permissions
from user_auth_app.models import UserProfile
from .serializers import UserProfileSerializer, RegistrationSerializer, UserDetailSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken

User = get_user_model()

class UserProfileList(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        saved_account = serializer.save()

        token, created = Token.objects.get_or_create(user=saved_account)
        
        data = {
            'token': token.key,
            'username': saved_account.username,
            'email': saved_account.email,
        }
        
        return Response(data, status=status.HTTP_201_CREATED)
    
class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        data =  {}
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key,
                'username': user.username,
                'email': user.email
            }
        else:
            data=serializer.errors

        return Response(data)
    

class EmailCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email', None)

        if not email:
            return Response(
                {"error": "Der 'email' Query-Parameter fehlt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:

            return Response(
                {"error": "E-Mail nicht gefunden. Der Benutzer existiert nicht."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserDetailSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)