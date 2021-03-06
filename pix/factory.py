"""
PIX class factory module.
"""


class Factory(object):
    """
    A Factory is repsonsible for dynamically building dict-like objects from
    the data returned from the PIX endpoints. Additionally these dynamically
    built objects can have base class(es) registered for them that can supply
    additional helper methods or behaviors. This allows for a more
    object-oriented interface and reduces the complexity of the large data
    structures returned from PIX.

    A base class for a given PIX class can be registered via the `register`
    method given the PIX class name. Any structure (dict) returned from a PIX
    request that contains a key 'class' is premoted to an object using any
    registered base classes (or ``pix.model.PIXObject`` if there are none
    registered).
    """
    # registered bases
    _registered = {}

    def __init__(self, session):
        """
        Parameters
        ----------
        session : ``pix.api.Session``
        """
        self.session = session

    @classmethod
    def register(cls, pixCls):
        """
        Decorator for registering an new PIX base class.

        Parameters
        ----------
        pixCls : str
            PIX class name. e.g. 'PIXImage'
        """
        def _deco(klass):
            bases = cls._registered.get(pixCls, [])
            bases.append(klass)
            cls._registered[pixCls] = bases
            return klass

        return _deco

    @classmethod
    def get_pix_cls(cls, name):
        """
        Build a pix object class with the given name. Any registered bases
        keyed for `name` will be used or the base ``pix.model.PIXObject``
        class.

        Parameters
        ----------
        name : str
            PIX class name. e.g. 'PIXImage'

        Returns
        -------
        Type[``pix.model.PIXObject``]
        """
        import pix.model
        # look for registered base classes and if none use the base object
        bases = cls._registered.get(str(name), [pix.model.PIXObject])
        obj = type(str(name), tuple(bases), {})
        obj.__name__ = str(name)
        return obj

    @classmethod
    def iter_contents(cls, data):
        """
        Iter the immediate contents of `data` and yield any dictionaries.
        Does not recurse.

        Parameters
        ----------
        data : dict

        Yields
        ------
        dict
        """
        for k, v in data.iteritems():
            if isinstance(v, dict):
                yield v
            elif isinstance(v, (set, list, tuple)):
                for l in v:
                    if isinstance(l, dict):
                        yield l

    def iter_children(self, data, recursive=True):
        """
        Iterate over the children objects of `data`.

        Parameters
        ----------
        data : dict
        recursive : bool
            Recursively look into generated objects and include their children
            too.

        Yields
        ------
        ``pix.model.PIXObject``
        """
        pixCls = data.get('class')
        if pixCls:
            obj = self.get_pix_cls(pixCls)
            yield obj(self, data)
        if recursive:
            for x in self.iter_contents(data):
                for obj in self.iter_children(x):
                    yield obj

    def objectfy(self, data):
        """
        Replace any viable structures with ``pix.model.PIXObject``.
        """
        if isinstance(data, dict):
            objCls = data.get('class')
            if objCls:
                obj = self.get_pix_cls(objCls)
                return obj(self, data)
            else:
                return {k: self.objectfy(v) for k, v in data.iteritems()}
        elif isinstance(data, (tuple, list, set)):
            results = [self.objectfy(x) for x in data]
            if isinstance(data, tuple):
                results = tuple(results)
            elif isinstance(data, set):
                results = set(results)
            return results
        else:
            return data
