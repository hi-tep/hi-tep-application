from connexion.jsonifier import Jsonifier
from flask.json.provider import DefaultJSONProvider

from hitep.openapi_server.models.base_model import Model


class JSONEncoder(Jsonifier):
    include_nulls = False

    def dumps(data, **kwargs):
        if isinstance(data, Model):
            dikt = {}
            for attr in data.openapi_types:
                value = getattr(data, attr)
                if value is None and not JSONEncoder.include_nulls:
                    continue
                attr = data.attribute_map[attr]
                dikt[attr] = value

            return dikt

        return DefaultJSONProvider.default(data)
