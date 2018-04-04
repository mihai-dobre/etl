import datetime
import pytz
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
# from ..log import log_base_view as log


class BaseView(ListAPIView):
    """
        ### Base view. It is inherited by all other views.
    """
    authentication_classes = ()
    permission_classes = ()
    paginate_by_param = 'page_size'

    def get_queryset(self):
        """
        Method used to filter the queryset based on url params: start_date, end_date
        :return:
        """
        if self.__class__.__name__ == 'DeviceView':
            from ..log import log_device as log
        elif self.__class__.__name__ == 'BrowserView':
            from ..log import log_browser as log
        elif self.__class__.__name__ == 'OpSysView':
            from ..log import log_op_sys as log
        start_timestamp = self.request.GET.get('start_date', None)
        end_timestamp = self.request.GET.get('end_date', None)
        if start_timestamp:
            start_datetime = datetime.datetime.fromtimestamp(int(start_timestamp)).astimezone(tz=pytz.utc)
            log.info('start_date %s', start_datetime)
            self.queryset = self.queryset.filter(timestamp__gte=start_datetime)
        if end_timestamp:
            end_datetime = datetime.datetime.fromtimestamp(int(end_timestamp)).astimezone(tz=pytz.utc)
            log.info('end_date %s', end_datetime)
            self.queryset = self.queryset.filter(timestamp__lt=end_datetime)
        log.info('queryset: %s', self.queryset)
        return self.queryset

    def get(self, request):
        """
        Method used to get information about the OS used.
        """
        # log.info("GET [%s] start processing.", self.request.path)
        # log.info('GET [%s] completed.', self.request.path)
        return Response(self.paginate_queryset(self.get_queryset()), status=200)
