# -*- coding: utf-8 -*-
from __future__ import absolute_import
import inspect
import sys
import types
import warnings
from fabric.tasks import WrappedCallableTask

def task_method(*args, **kwargs):
    """
    Decorator declaring the wrapped method to be task.

    It accepts the same arguments as ``fabric.decorators.task`` so
    use it on methods just like fabric's decorator is used on functions.

    The class decorated method belongs to should be a subclass
    of :class:`.TaskSet`.
    """

    invoked = bool(not args or kwargs)
    if not invoked:
        func, args = args[0], ()

    def decorator(func):
        func._task_info = dict(
            args = args,
            kwargs = kwargs
        )
        return func

    return decorator if invoked else decorator(func)

def task(*args, **kwargs):
    msg = "@taskset.task decorator is deprecated and will be removed soon; please use @taskset.task_method instead."
    warnings.warn(msg, DeprecationWarning)
    return task_method(*args, **kwargs)


class TaskSet(object):
    """
    TaskSet is a class that can expose its methods as Fabric tasks.

    Example::

        # fabfile.py
        from fabric.api import local
        from taskset import TaskSet, task_method

        class SayBase(TaskSet):
            def say(self, what):
                raise NotImplemented()

            @task_method(default=True, alias='hi')
            def hello(self):
                self.say('hello')

        class EchoSay(SayBase):
            def say(self, what):
                local('echo ' + what)

        say = EchoSay().expose_as_module('say')

    and then::

        $ fab say.hi
    """

    def expose_to(self, module_name):
        """
        Adds tasks to module which name is passed in ``module_name`` argument.
        Returns a list of added tasks names.

        Example::

            instance = MyTaskSet()
            __all__ = instance.expose_to(__name__)
        """
        module_obj = sys.modules[module_name]
        return self._expose_to(module_obj)

    def expose_to_current_module(self):
        """
        The same as :meth:`TaskSet.expose_to` but magically
        addds tasks to current module.

        Example::

            instance = MyTaskSet()
            __all__ = instance.expose_to_current_module()
        """
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        return self.expose_to(mod.__name__)

    def expose_as_module(self, module_name, module_type=types.ModuleType):
        """
        Creates a new module of type ``module_type`` and named ``module_name``,
        populates it with tasks and returns this newly created module.
        """
        module = module_type(module_name)
        self._expose_to(module)
        return module

    def _expose_to(self, module_obj):
        task_list = []
        for name, task in self._get_fabric_tasks():
            setattr(module_obj, name, task)
            task_list.append(name)
        return task_list

    def _is_task(self, func):
        return hasattr(func, '_task_info')

    def _task_for_method(self, method):
        return WrappedCallableTask(method, *method._task_info['args'], **method._task_info['kwargs'])

    def _get_fabric_tasks(self):
        return (
            (name, self._task_for_method(task))
            for name, task in inspect.getmembers(self, self._is_task)
        )
