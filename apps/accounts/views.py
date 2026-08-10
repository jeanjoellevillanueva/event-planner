"""
Views for accounts app.
"""

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.accounts.serializers import BusinessMembershipSerializer
from apps.accounts.serializers import InvitationAcceptSerializer
from apps.accounts.serializers import InvitationCreateSerializer
from apps.accounts.serializers import InvitationRegisterSerializer
from apps.accounts.serializers import InvitationSerializer
from apps.accounts.serializers import SwitchBusinessSerializer
from apps.accounts.serializers import UserRegistrationSerializer
from apps.accounts.serializers import UserSerializer
from apps.accounts.serializers import UserUpdateSerializer
from apps.common.permissions import IsBusinessAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Create user and return tokens.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for current user profile.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Return current user.
        """
        return self.request.user

    def get_serializer_class(self):
        """
        Use update serializer for PUT/PATCH.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


class UserBusinessesView(generics.ListAPIView):
    """
    API endpoint to list user's businesses.
    """

    serializer_class = BusinessMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return memberships for current user.
        """
        return self.request.user.business_memberships.select_related('business')


class SwitchBusinessView(APIView):
    """
    API endpoint to switch current business.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Switch user's current business.
        """
        serializer = SwitchBusinessSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        business_id = serializer.validated_data['business_id']
        membership = request.user.business_memberships.get(business_id=business_id)

        request.user.current_business = membership.business
        request.user.save(update_fields=['current_business'])

        return Response({
            'message': 'Business switched successfully',
            'current_business': {
                'id': membership.business.id,
                'name': membership.business.name,
                'role': membership.role
            }
        })


class InvitationListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create invitations.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_queryset(self):
        """
        Return invitations for current business.
        """
        return Invitation.objects.filter(
            business=self.request.user.current_business
        ).select_related('invited_by')

    def get_serializer_context(self):
        """
        Add business to context.
        """
        context = super().get_serializer_context()
        context['business'] = self.request.user.current_business
        return context

    def perform_create(self, serializer):
        """
        Create invitation and send email.
        """
        invitation = serializer.save()
        self.send_invitation_email(invitation)

    def send_invitation_email(self, invitation):
        """
        Send invitation email to invitee.
        """
        subject = f"You've been invited to join {invitation.business.name}"
        message = render_to_string('emails/invitation.html', {
            'invitation': invitation,
            'accept_url': f"/invitations/{invitation.token}/"
        })
        send_mail(
            subject,
            message,
            None,
            [invitation.email],
            html_message=message,
            fail_silently=True
        )


class InvitationDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get invitation details by token (public).
    """

    serializer_class = InvitationSerializer
    permission_classes = [AllowAny]
    lookup_field = 'token'

    def get_queryset(self):
        """
        Return pending invitations.
        """
        return Invitation.objects.filter(status='pending')

    def retrieve(self, request, *args, **kwargs):
        """
        Get invitation with validity check.
        """
        invitation = self.get_object()

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {'error': 'Invitation has expired'},
                status=status.HTTP_410_GONE
            )

        return super().retrieve(request, *args, **kwargs)


class InvitationAcceptView(APIView):
    """
    API endpoint to accept invitation.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        """
        Accept invitation for authenticated user.
        """
        try:
            invitation = Invitation.objects.get(token=token, status='pending')
        except Invitation.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired invitation'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {'error': 'Invitation has expired'},
                status=status.HTTP_410_GONE
            )

        if invitation.email != request.user.email:
            return Response(
                {'error': 'Invitation email does not match your account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if BusinessMembership.objects.filter(
            user=request.user,
            business=invitation.business
        ).exists():
            return Response(
                {'error': 'You are already a member of this business'},
                status=status.HTTP_400_BAD_REQUEST
            )

        BusinessMembership.objects.create(
            user=request.user,
            business=invitation.business,
            role=invitation.role
        )

        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=['status', 'accepted_at'])

        if not request.user.current_business:
            request.user.current_business = invitation.business
            request.user.save(update_fields=['current_business'])

        return Response({
            'message': 'Invitation accepted successfully',
            'business': {
                'id': invitation.business.id,
                'name': invitation.business.name,
                'role': invitation.role
            }
        })


class InvitationRegisterView(APIView):
    """
    API endpoint to register via invitation.
    """

    permission_classes = [AllowAny]

    def post(self, request, token):
        """
        Register new user via invitation.
        """
        try:
            invitation = Invitation.objects.get(token=token, status='pending')
        except Invitation.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired invitation'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {'error': 'Invitation has expired'},
                status=status.HTTP_410_GONE
            )

        if User.objects.filter(email=invitation.email).exists():
            return Response(
                {'error': 'User with this email already exists. Please login to accept.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvitationRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.create_user(
            email=invitation.email,
            username=serializer.validated_data['username'],
            phone=serializer.validated_data.get('phone', ''),
            timezone=serializer.validated_data.get('timezone', 'UTC')
        )
        user.set_password(serializer.validated_data['password'])
        user.save()

        BusinessMembership.objects.create(
            user=user,
            business=invitation.business,
            role=invitation.role
        )

        user.current_business = invitation.business
        user.save(update_fields=['current_business'])

        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=['status', 'accepted_at'])

        return Response({
            'message': 'Registration and invitation acceptance successful',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
