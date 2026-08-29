"""
Views for contracts app.
"""

from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdmin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember
from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate
from apps.contracts.serializers import ContractGenerateSerializer
from apps.contracts.serializers import ContractSerializer
from apps.contracts.serializers import ContractSignSerializer
from apps.contracts.serializers import ContractTemplateCreateSerializer
from apps.contracts.serializers import ContractTemplateListSerializer
from apps.contracts.serializers import ContractTemplateSerializer


class ContractTemplateListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create contract templates.
    """

    queryset = ContractTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return ContractTemplateCreateSerializer
        if self.request.query_params.get('list', '').lower() == 'true':
            return ContractTemplateListSerializer
        return ContractTemplateSerializer


class ContractTemplateDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for template detail operations.
    """

    queryset = ContractTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ContractTemplateCreateSerializer
        return ContractTemplateSerializer


class ContractListView(generics.ListAPIView):
    """
    API endpoint to list contracts.
    """

    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsBusinessMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['booking__client__name', 'notes']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return contracts for current business.
        """
        return Contract.objects.filter(
            booking__business=self.request.user.current_business
        ).select_related('booking', 'booking__client', 'template', 'generated_by')


class ContractDetailView(generics.RetrieveAPIView):
    """
    API endpoint for contract detail.
    """

    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get_queryset(self):
        """
        Return contracts for current business.
        """
        return Contract.objects.filter(
            booking__business=self.request.user.current_business
        ).select_related('booking', 'booking__client', 'template', 'generated_by')


class ContractGenerateView(APIView):
    """
    API endpoint to generate a contract for a booking.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request, booking_id):
        """
        Generate contract for a booking.
        """
        try:
            booking = Booking.objects.get(
                pk=booking_id,
                business=request.user.current_business
            )
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ContractGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template_id = serializer.validated_data.get('template_id')
        if template_id:
            try:
                template = ContractTemplate.objects.get(
                    pk=template_id,
                    business=request.user.current_business,
                    is_active=True
                )
            except ContractTemplate.DoesNotExist:
                return Response(
                    {'error': 'Template not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            template = ContractTemplate.objects.filter(
                business=request.user.current_business,
                is_default=True,
                is_active=True
            ).first()

            if not template:
                return Response(
                    {'error': 'No default template found. Please specify a template.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        contract = Contract.objects.create(
            booking=booking,
            template=template,
            generated_by=request.user,
            notes=serializer.validated_data.get('notes', ''),
            status='generated'
        )

        contract.render_content()
        contract.save(update_fields=['rendered_content'])

        from apps.contracts.pdf import queue_contract_pdf
        queue_contract_pdf(contract.id)

        return Response({
            'message': 'Contract generated successfully',
            'contract': ContractSerializer(contract, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class ContractDownloadView(APIView):
    """
    API endpoint to download contract PDF.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get(self, request, pk):
        """
        Download contract file.
        """
        try:
            contract = Contract.objects.get(
                pk=pk,
                booking__business=request.user.current_business
            )
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not contract.generated_file:
            return Response({
                'rendered_content': contract.rendered_content,
                'message': 'PDF not yet generated. Returning HTML content.'
            })

        return FileResponse(
            contract.generated_file,
            as_attachment=True,
            filename=f"contract_{contract.id}.pdf"
        )


class ContractSignView(APIView):
    """
    API endpoint to mark contract as signed.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request, pk):
        """
        Mark contract as signed.
        """
        try:
            contract = Contract.objects.get(
                pk=pk,
                booking__business=request.user.current_business
            )
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if contract.status == 'signed':
            return Response(
                {'error': 'Contract is already signed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ContractSignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract.status = 'signed'
        contract.signed_at = timezone.now()
        contract.signed_by = serializer.validated_data['signed_by']

        if 'signed_file' in serializer.validated_data:
            contract.signed_file = serializer.validated_data['signed_file']

        contract.save()

        return Response({
            'message': 'Contract marked as signed',
            'contract': ContractSerializer(contract, context={'request': request}).data
        })
