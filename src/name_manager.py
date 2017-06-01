# -*- coding: utf-8 -*-

from ast import literal_eval

class Singleton:
    """A non-thread-safe helper class to implement singletons.
    It should be used as a decorator (not a metaclass) to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, the `Instance` method must be used.
    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. On first call, it creates a new
        instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.
        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through Instance().')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

@Singleton
class NameManager:
    """Class for managing associations of name <-> object in a program.
    Uses the namespace concept for registering/unregistering names.
    """

    def __init__(self):
       print 'NameManager created'
       # A namespace is a sequence of pairs of "name": Object
       self._namespaces = [{}]

    def register(self, name, obj, namespace_idx=0):
        """NOTE: Namespace list is extended one element at a time, it doesn't
        matter the namespace_idx if it's between len(self._namespaces) and
        infinite, the list is always incremented by 1.
        """
        if namespace_idx >= len(self._namespaces):
            self._namespaces.append({})
            namespace_idx = len(self._namespaces) - 1
        namespace = self._namespaces[namespace_idx]
        namespace[name] = obj
        print 'Name', name, 'registered.'

    def unregister(self, name, namespace_idx=0):
        namespace = self._namespaces[namespace_idx]
        namespace.pop(name)
        print 'Name', name, 'unregistered.'

    def clear(self, namespace_idx=0):
        namespace = self._namespaces[namespace_idx]
        namespace.clear()

    def get(self, name, namespace_idx=0):
        namespace = self._namespaces[namespace_idx]
        return namespace[name]

    def get_all(self, namespace_idx=0):
        try:
            namespace = self._namespaces[namespace_idx]
            return [(key, namespace[key]) for key in namespace]
        except IndexError:
            return []

class NameParser:
    """Class for parsing a list of names or lines from a loaded file or string.
    Specifications must be in the format:

    #name: 'AtomName', [Hook0Value, Hook1Value, Hook2Value, Hook3Value], IsConstantValue

    #line: LineId, {Hook0Id: [HookIds, ...], Hook2Id: [HookIds, ...], ...}
    """

    TOKENS = {'name': '#name:',
              'line': '#line:'}

    @staticmethod
    def str_to_bool(s):
        if s == 'True':
            return True
        elif s == 'False':
            return False
        else:
            raise ValueError("Cannot covert {} to a bool".format(s))

    @classmethod
    def parse_name(cls, line):
        name = ''
        hooks = []

        data = line.lstrip(cls.TOKENS['name'])
        data = data.lstrip()
        get_3_values = (lambda t: t if len(t) == 3 else (t[0], t[1], False))
        name, hooks, is_constant = get_3_values(literal_eval(data))

        if (name == '') or (len(hooks) != 4):
            raise AssertionError("Wrong name specification: {}".format(line))

        return name, hooks, is_constant

    @classmethod
    def parse_line(cls, line):
        line_id = None
        graph = None

        data = line.lstrip(cls.TOKENS['line'])
        data = data.lstrip()
        line_id, graph = literal_eval(data)

        if (line_id is None) or (graph is None):
            raise AssertionError("Wrong line specification: {}".format(line))

        return line_id, graph

    @classmethod
    def get_name_str(cls, name, hooks, is_constant=False):
        s = cls.TOKENS['name'] + " '{0}', [{1}, {2}, {3}, {4}], {5}\n".format(
            name,
            str(hooks[0]), str(hooks[1]), str(hooks[2]), str(hooks[3]),
            str(is_constant))
        return s

    @classmethod
    def get_line_str(cls, line_id, graph):
        s = cls.TOKENS['line'] + ' ' + str(line_id) + ', ' + str(graph) + '\n'
        return s
