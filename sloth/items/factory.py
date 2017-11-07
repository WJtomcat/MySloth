from sloth.core.utils import import_callable

class Factory:
    def __init__(self, items=None):
        self._items = {}
        if items is not None:
            for _type, item in items.items():
                self.register(_type, item, replace=True)

    def register(self, _type, item, replace=False):
        _type = str(_type)
        if _type in self._items and not replace:
            raise Exception("Type already has an item")
        else:
            if type(item) == str:
                item = import_callable(item)
            self._items[_type] = item

    def clear(self, _type=None):
        if _type is None:
            self._items = {}
        else:
            _type = str(_type)
            if _type in self._items:
                del self._items[_type]

    def create(self, _type, *args, **kwargs):
        _type = str(_type)
        if _type not in self._items:
            return None
        item = self._items[_type]
        if item is None:
            return None
        return item(*args, **kwargs)