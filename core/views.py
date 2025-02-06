# core/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .zabbix_utils import get_router_interfaces

class ZabbixInterfaceDataView(APIView):
    """
    API endpoint to get router interface data from Zabbix.
    """

    def get(self, request, format=None):
        try:
            interfaces = get_router_interfaces()
            return Response(interfaces, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
