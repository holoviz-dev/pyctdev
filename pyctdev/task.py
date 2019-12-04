"""
"""

import param

from .util import log_warning

from . import _doithacks

# TODO: this was only ever a sketch; don't know if it's a good idea or not :)


class DoitTask(param.Parameterized):
    """Refer to doit's documentation etc.

    Some things to note:

      * functions used to build up command strings might be called
        several times by doit while it's constructing tasks

    """
    read_only = param.Boolean(default=False)

    # TODO: pick right param types, e.g. classselector.
    # TODO: add docs
    task_type = param.Parameter()
    additional_doc = param.String() # Anything specific to the implementation of the task i.e. beyond the abstract task defition
    uptodate = param.Parameter()
    actions = param.List()
    params = param.List()
    teardown = param.List(default=None)
    file_dep = param.List(default=None)
    task_dep = param.List()
    targets = param.List(default=None)
    getargs = param.Parameter()

    def create_doit_tasks(self):
        return self.__call__()

    def __call__(self):
        # TODO: split this up!

        # check params as expected from defn
        my_params = set([p['name'] for p in self.params])
        expected_params = set(self.task_type.params)
        if not my_params.issuperset(expected_params):
            # TODO: warning not heplful for a user of the task - this
            # is for a developer of the task

            # TODO: and what if a specific backend wants to provide an
            # extra option. Should probably check that implementation
            # is a superset of params
            log_warning(
                "Task type %s (from ecosystem=%s) should have params %s but got %s",
                self.task_type.__name__,
                self._ecosystem if hasattr(
                    self,
                    '_ecosystem') else "unknown",
                expected_params,
                my_params)

        # build up full docs
        docs = [self.task_type.__doc__, self.additional_doc, "task type: %s.%s\n" % (
            self.task_type.__module__, self.task_type.__name__)]

        doit_task = {'actions': self.actions,
                     'params': self.params,
                     'doc': "\n\n".join(d for d in docs if d is not None),
                     'getargs': self.getargs,
                     'task_dep': self.task_dep}

        doit_task['uptodate'] = [_doithacks.populate_task_options]
        # are these ifs necessary? won't default do (i.e. isn't None ok for
        # doit)? and could surely automate
        if self.teardown is not None:
            doit_task['teardown'] = self.teardown
        if self.uptodate is not None:
            doit_task['uptodate'] += self.uptodate
        if self.file_dep is not None:
            doit_task['file_dep'] = self.file_dep
        if self.targets is not None:
            doit_task['targets'] = self.targets

        return doit_task
