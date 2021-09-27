from . import models
from . import wizards
from . import controllers

# Monkey Patch Json Request because odoo is using 10 year old
# json-rpc as a default 'application/json' http header handler.. :(
# https://techinplanet.com/how-to-set-response-status-code-in-route-with-type-json-in-odoo-14/
# -- this is a mess --
# https://github.com/odoo/odoo/issues/7766#issuecomment-331908531
from odoo.http import JsonRequest, Response
from odoo.tools import date_utils
from werkzeug.wrappers import Response as werkzeugResponse
import logging, json

_logger = logging.getLogger(__name__)

class JsonRequestPatch(JsonRequest):
    def _json_response(self, result=None, error=None):
        # =====================================================================
        # Monkey Patch Code
        # This will take a standard http werkzeug response look in the headers
        # for the X-MP-Odoo-JSON item and if it's TRUE just pass it through
        # instead of odoo's jsonrpc thing..
        # I'm hoping this won't interrupt any other Odoo JSON RPC items..
        # =====================================================================
        if isinstance(result, werkzeugResponse):
            hdrs = result.headers
            if hdrs.get('X-MP-Odoo-JSON') == "TRUE":
                # We don't want this in the Response out..
                del result.headers['X-MP-Odoo-JSON']
                return result
        # =====================================================================
        # End Monkey Patch Code
        # =====================================================================

        response = {
            'jsonrpc': '2.0',
            'id': self.jsonrequest.get('id')
            }

        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result

        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )

JsonRequest._json_response = JsonRequestPatch._json_response
