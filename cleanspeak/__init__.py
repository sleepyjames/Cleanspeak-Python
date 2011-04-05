import simplejson
import re
import urllib2
from urllib import urlencode
import simplejson 

DEFAULT_API_ENDPOINT = "http://api.inversoft.com:8001/content/handle.js"

# If were using django then 
# try an import the api key and endpoint from a settings file

try:
    from django.conf import settings
    API_KEY = getattr(settings, 'CLEANSPEAK_API_KEY', None)
    API_ENDPOINT = getattr(settings, 'CLEANSPEAK_API_ENDPOINT', DEFAULT_API_ENDPOINT)
    CLEANSPEAK_OPTIONS = getattr(settings, 'CLEANSPEAK_OPTIONS', {})
except ImportError:
    API_KEY = None
    API_ENDPOINT = DEFAULT_API_ENDPOINT
    CLEANSPEAK_OPTIONS = {}


DEFAULT_PARAMS = {
    #'request.filter.cleanspeakdb.locale' : 'en-GB',
    'request.filter.cleanspeakdb.enabled' : 'true',
    'request.filter.emails.enabled' : 'true',
    'request.filter.urls.enabled' : 'true',
    #'request.filter.phone_numbers.enabled' : 'true',
    'request.filter.enabled' : 'true',
    'request.filter.operation' : 'replace',
    'request.filter.cleanspeakdb.severity' : 'high',
}
DEFAULT_PARAMS.update(CLEANSPEAK_OPTIONS)


class CleanSpeakException(Exception):
    pass


class CleanSpeakResult(object):
    """ Wraps a result from the Cleanspeak API 
    """
    original = ""
    filtered = ""
    matched = False
    matches = []
    locations = []

    def __init__(self, data, original):
        self.original = original
        self.matched = data['filter']['matched']
        self.matches = data['filter']['matches']
        self.data = data


class CleanSpeakMatchResult(CleanSpeakResult):
    def __init__(self, data, original):
        super(CleanSpeakMatchResult, self).__init__(data, original)
        self.filtered = self.data['filter']['filtered']
 

class CleanSpeakLocateResult(CleanSpeakResult):
    def __init__(self, data, original):
        super(CleanSpeakLocateResult, self).__init__(data, original)


class CleanSpeakReplaceResult(CleanSpeakResult):
    def __init__(self, data, original):
        super(CleanSpeakReplaceResult, self).__init__(data, original)
        self.replacement = self.data['filter']['replacement']


class CleanSpeak(object):
    """ Wrapper to the Cleanspeak REST web service 

        Valid options are listed here
        http://www.inversoft.com/docs/technical/free/webservice-content-handling
    """

    operation_result_class = {
        'match' : CleanSpeakMatchResult,
        'locate' : CleanSpeakLocateResult,
        'replace' : CleanSpeakReplaceResult,
    }

    @classmethod
    def _make_request(cls, content, operation='match', api_key=API_KEY, 
                      api_endpoint=API_ENDPOINT):

        """ Encapulates a request to the CleanSpeak API
        """

        if api_key is None:
            raise CleanSpeakException(u'You need to supply an api key')

        data = DEFAULT_PARAMS.copy()
        data.update({
            'request.content' : content, 
            'request.filter.operation' : operation
        })

        try:
            req = urllib2.Request(API_ENDPOINT, urlencode(data))
            req.add_header("Content-Type", "application/x-www-form-urlencoded");
            req.add_header("Authentication", api_key)
            response = urllib2.urlopen(req)
            ret = response.read()
        except urllib2.URLError: 
            raise CleanSpeakException(u'Unable to process cleanspeak api request')

        # Cleanspeak does not escpace the single quote in its JSON response
        # so we manually replace it here
        ret = ret.replace("\\'", "'")

        try:
            json = simplejson.loads(ret)
        except ValueError:
            raise CleanSpeakException(u'Could not decode JSON response from api')
        
        resultClass = CleanSpeak.operation_result_class[operation]
        
        return resultClass(data=json, original=content)

    @classmethod
    def replace(cls, content, **kwargs):
        """ Wrapper for the cleanspeak replace method """
        return CleanSpeak._make_request(content, operation="replace", **kwargs)

    @classmethod
    def locate(cls, content, **kwargs):
        """ Wrapper for the cleanspeak locate method """
        return CleanSpeak._make_request(content, operation="locate", **kwargs)

    @classmethod
    def match(cls, content, **kwargs):
        """ Wrapper for the cleanspeak locate method """
        return CleanSpeak._make_request(content, operation="match", **kwargs)
