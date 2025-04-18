from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from hitep.openapi_server.models.base_model import Model
from hitep.openapi_server.models.model3_d_coordinate import Model3DCoordinate
from hitep.openapi_server import util

from hitep.openapi_server.models.model3_d_coordinate import Model3DCoordinate  # noqa: E501

class PositionChange(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, previous=None, current=None, timestamp=None):  # noqa: E501
        """PositionChange - a model defined in OpenAPI

        :param previous: The previous of this PositionChange.  # noqa: E501
        :type previous: Model3DCoordinate
        :param current: The current of this PositionChange.  # noqa: E501
        :type current: Model3DCoordinate
        :param timestamp: The timestamp of this PositionChange.  # noqa: E501
        :type timestamp: datetime
        """
        self.openapi_types = {
            'previous': Model3DCoordinate,
            'current': Model3DCoordinate,
            'timestamp': datetime
        }

        self.attribute_map = {
            'previous': 'previous',
            'current': 'current',
            'timestamp': 'timestamp'
        }

        self._previous = previous
        self._current = current
        self._timestamp = timestamp

    @classmethod
    def from_dict(cls, dikt) -> 'PositionChange':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The PositionChange of this PositionChange.  # noqa: E501
        :rtype: PositionChange
        """
        return util.deserialize_model(dikt, cls)

    @property
    def previous(self) -> Model3DCoordinate:
        """Gets the previous of this PositionChange.


        :return: The previous of this PositionChange.
        :rtype: Model3DCoordinate
        """
        return self._previous

    @previous.setter
    def previous(self, previous: Model3DCoordinate):
        """Sets the previous of this PositionChange.


        :param previous: The previous of this PositionChange.
        :type previous: Model3DCoordinate
        """
        if previous is None:
            raise ValueError("Invalid value for `previous`, must not be `None`")  # noqa: E501

        self._previous = previous

    @property
    def current(self) -> Model3DCoordinate:
        """Gets the current of this PositionChange.


        :return: The current of this PositionChange.
        :rtype: Model3DCoordinate
        """
        return self._current

    @current.setter
    def current(self, current: Model3DCoordinate):
        """Sets the current of this PositionChange.


        :param current: The current of this PositionChange.
        :type current: Model3DCoordinate
        """
        if current is None:
            raise ValueError("Invalid value for `current`, must not be `None`")  # noqa: E501

        self._current = current

    @property
    def timestamp(self) -> datetime:
        """Gets the timestamp of this PositionChange.

        Date of presence at the current position  # noqa: E501

        :return: The timestamp of this PositionChange.
        :rtype: datetime
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime):
        """Sets the timestamp of this PositionChange.

        Date of presence at the current position  # noqa: E501

        :param timestamp: The timestamp of this PositionChange.
        :type timestamp: datetime
        """

        self._timestamp = timestamp
