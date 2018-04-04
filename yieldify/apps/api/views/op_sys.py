from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from django.utils import timezone
from ..models import Request
from ..log import log_op_sys as log


class OpSysView(ListAPIView):
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
    authentication_classes = ()
    permission_classes = ()
    queryset = Request.objects.all().values('id', 'timestamp', 'user__user_id', 'agent__op_sys', 'agent__op_sys_version')
    paginate_by_param = 'page_size'

    def get(self, *args, **kwargs):
        """
        Method used to get information about the OS used.
        """
        log.info("GET [%s] start processing.", self.request.path)
        log.info("GET args: %s", kwargs)

        start_time = int(timezone.now().timestamp())
        log.info('GET [%s] completed in %s seconds.', self.request.path, int(timezone.now().timestamp() - start_time))
        return Response(self.paginate_queryset(self.get_queryset()), status=200)
