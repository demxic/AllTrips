import datetime
import json
from models.timeclasses import datetime_format

def object_encode(an_object):
    if isinstance(an_object, datetime.datetime):
        fmt = datetime_format
        return dict(__class__="datetime.datetime.strptime",
                    __args__=[],
                    __kw__=dict(
                        iata_code=an_object.iata_code,
                        zone=an_object.timezone.zone,
                        viaticum=an_object.viaticum)
                    )
    else:
        return json.JSONEncoder.default(an_object)


def object_decode(some_dict: dict):
    if set(some_dict.keys()) == {"__class__", "__args__", "__kw__"}:
        class_ = eval(some_dict['__class__'])
        return class_(*some_dict['__args__'], **some_dict['__kw__'])
    else:
        return some_dict
