from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from ..log import log_browser as log


class DeviceView(APIView):
    """
        ### API endpoint for getting a list of used devices.
        curl example: `curl -v -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:8000/stats/device/`
        <br>
        The user can specify a time span using some url parameters:

        * start_date=timestamp

        * end_date=timestamp

        curl example with parameters:
            `curl -v -H "Accept: application/json"
                     -H "Content-Type: application/json"
                    http://localhost:8000/stats/device/&start_date=timestamp&end_date=timestamp`

        **Live endpoint is available by clicking on the plug icon on the top-right side of the endpoint's bar.**
    """
    authentication_classes = ()
    permission_classes = ()

    def get(self, *args, **kwargs):
        """
        Method used to get information about the browsers used.
        """
        log.info("GET [%s] start processing.", self.request.path)
        log.info("GET args: %s", kwargs)

        start_time = int(timezone.now().timestamp())

        log.info('GET [%s] completed in %s seconds.', self.request.path, int(timezone.now().timestamp() - start_time))
        return Response({'device': 'all ok'}, status=200)
