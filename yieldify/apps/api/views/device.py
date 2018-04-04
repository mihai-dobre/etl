from .base_view import BaseView
from ..models import Request


class DeviceView(BaseView):
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
    queryset = Request.objects.all().values('id', 'timestamp', 'user__user_id', 'agent__device',
                                            'agent__device_type', 'agent__device_brand')
