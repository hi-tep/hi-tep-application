import collections

from connexion.jsonifier import Jsonifier

from hitep.openapi_server.models.base_model import Model


class JSONEncoder(Jsonifier):
    def __init__(self, include_nulls=False, **kwargs):
        super().__init__(**kwargs)
        self._include_nulls = False

    def dumps(self, data, **kwargs):
        if isinstance(data, Model):
            dikt = self._to_dict(data, **kwargs)
            return super().dumps(dikt, **kwargs)

        return super().dumps(data, **kwargs)

    def _to_dict(self, data, **kwargs):
        if isinstance(data, (bool, str, int, float, bytes, type(None))):
            return data

        if isinstance(data, (list, tuple)):
            return [self._to_dict(x) for x in data]

        if isinstance(data, Model):
            dikt = {}
            for attr in data.openapi_types:
                value = getattr(data, attr)
                if value is None and not self._include_nulls:
                    continue
                attr = data.attribute_map[attr]
                dikt[attr] = self._to_dict(value, **kwargs)

            return dikt

        return data
