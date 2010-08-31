from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.db.models.query import QuerySet
from django.utils import simplejson as json
from piston.emitters import Emitter
from piston.validate_jsonp import is_valid_jsonp_callback_value


class DojoDataEmitter(Emitter):

    def render(self, request):
        """
        Renders dojo.data compatible JSON if self.data is a QuerySet, falls
        back to standard JSON. Requires your handler to expose the `id`
        field of your model, that Piston excludes per default. The item's
        label is the unicode representation of your model unless it already
        has a field with the name `_unicode`.

        Optional GET variables:
            `callback`: JSONP callback
            `indent`: Number of spaces for JSON indentation
        """
        callback = request.GET.get('callback', None)
        try:
            indent = int(request.GET['indent'])
        except (KeyError, ValueError):
            indent = None

        data = self.construct()

        if isinstance(self.data, QuerySet):
            unicode_lookup_table = dict()
            [unicode_lookup_table.__setitem__(item.pk, unicode(item)) \
                for item in self.data.all()]

            for dict_item in data:
                try:
                    id = dict_item['id']
                except KeyError:
                    raise KeyError('The handler of the model that you want '\
                        'to emit as DojoData needs to expose the `id` field!')
                else:
                    dict_item.setdefault('_unicode', unicode_lookup_table[id])

            data = {
                'identifier': 'id',
                'items': data,
                'label': '_unicode',
                'numRows': len(data),
            }

        serialized_data = json.dumps(data, ensure_ascii=False,
            cls=DateTimeAwareJSONEncoder, indent=indent)

        # Callback
        if callback and is_valid_jsonp_callback_value(callback):
            return '%s(%s)' % (callback, serialized_data)

        return serialized_data


def register_emitters():
    Emitter.register('dojodata', DojoDataEmitter,
        'application/json; charset=utf-8')
