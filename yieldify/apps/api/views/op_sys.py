from django.db.models import F

from .base_view import BaseView
from ..models import Request


class OpSysView(BaseView):
    """
        ### API endpoint for getting a list of used operating systems.
        curl example: `curl -v -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:8000/stats/os/`
        <br>
        The user can specify a time span using some url parameters:

        * start_date=timestamp

        * end_date=timestamp

        curl example with parameters:
            `curl -v -H "Accept: application/json"
                     -H "Content-Type: application/json"
                    http://localhost:8000/stats/os/&start_date=timestamp&end_date=timestamp`

        **Live endpoint is available by clicking on the plug icon on the top-right side of the endpoint's bar.**
    """
    queryset = Request.objects.annotate(
        user_id=F('user__user_id'),
        os=F('agent__op_sys'),
        os_version=F('agent__op_sys_version')
        ).values(
        'id',
        'timestamp',
        'user_id',
        'os',
        'os_version')
