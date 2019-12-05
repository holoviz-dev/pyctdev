"""Hack doit; ideally, all things here would be in doit.

  * Promote params of a task's dependencies to be params of the task
    (otherwise, you need to specify the task and its dependencies to
    be able to specify a parameter). How? pyctdev.__main__ task loader
    goes through all tasks and their dependencies.

  * Support passing of a param once and having it apply to all tasks
    which have that param (whether they are explicitly listed or are
    dependencies). How? populate_task_options() put as first uptodate
    for all pyctdev tasks.

  * Support detection of missing but required parameters. How?  Monkey
    patch doit.cmdparse.TaskParse.parse.

  * Print the command that will be run before it's run. How? Subclass
    PythonAction, CommandAction. Not just after a command has failed.

  * Support limited dry_run. How? Subclass PythonAction, CommandAction.

  * Full docstring display in help (rather than just the first line,
    which is all doit stores. How? Preserve the full docstring by
    patching doit.task.Task._init_doc, and display by patching
    doit.cmd_help.Help. (Also: includes param help in 'help', which
    was previously only included in 'info' - so no need to run both.)

"""

# The other things you could maybe consider for _doithacks:
#
#   - custom task loader (pyctdev.__main__)
#
#   - pyctdev.task's DoitTask



# TODO: accidentally autopep8'd this file. Which will make it harder
# to see the changes from doit for PythonAction, CommandAction. Should
# be easy to restore manually.

# TODO: move this file to util?

import sys, getopt

from .util import log_message


#####################################

import doit.cmdparse
_orig_TaskParse_parse = doit.cmdparse.TaskParse.parse


def hackparse(self, in_args):
    # 1. this hack would be better in control.py, line 163 (in
    # add_filtered_task(), which is defined in _process_filter(), but
    # I couldn't see easy way to get it in there.
    #
    # 2. ideally should be feature of doit anyway    
    params, args = _orig_TaskParse_parse(self, in_args)
    missing_but_required = [pname for pname,
                            pval in params.items() if pval is NotImplemented]
    if missing_but_required:
        raise ValueError(
            "The following parameters are required by one or more of the tasks selected: %s" %
            missing_but_required)
    return params, args


log_message(
    "Monkey patching doit.cmdparse.TaskParse.parse to report missing but required parameters.")
doit.cmdparse.TaskParse.parse = hackparse

#####################################


######################################################################

# hack to add params of dependencies - otherwise, you can't just call
# a top-level task and supply a param that's required for a task you
# depend on. task authors would have to duplicate all the parameters
# of subtasks and passing all the parameters around.

def update_all_params(tasks):
    zed = {task.name: task for task in tasks}
    for t in tasks:
        tdep = []
        _get_all_deps(zed, t, tdep)
        _update_params(zed, t, tdep)


def _get_all_deps(tasks, task, task_dep):
    for t in task.task_dep:
        _get_all_deps(tasks, tasks[t], task_dep)
        task_dep.append(t)


def _update_params(tasks, task, task_dep):
    for t in task_dep:
        for p in tasks[t].params:
            if p not in task.params:
                task.params.append(p)


######################################################################

# hack to sneak in setting of task.options for dependencies. This fn
# is added as first uptodate for all tasks.
def populate_task_options(task,values):
    if task.options is None:
        # why hasn't options been set :( such a hack.
        log_message('(doithack) %s.options is None; setting now...'%task)
        #defaults
        task.options = {k['name']:k['default'] for k in task.params}
        #### bit 1
        args_no_vars = []
        for arg in sys.argv[1::]:
            if (arg[0] != '-') and ('=' in arg):
                pass
            else:
                args_no_vars.append(arg)
        #### bit 2
        tc = doit.cmdparse.TaskParse([doit.cmdparse.CmdOption(opt) for opt in task.params])
        if len(args_no_vars) > 0 and args_no_vars[0] == 'info':
            log_message("...not setting %s.options because I think we're in 'help'", task)
            return None # TODO: I just hacked this 'info' detection in so info will run for tasks with required args
        #### construct relevant argv
        taskopts = []
        while args_no_vars:
            opts, args = getopt.getopt(args_no_vars, tc.get_short(), tc.get_long())
            taskopts += opts
            if args:
                del args[0]
            args_no_vars = args
        relevant_argv = " ".join([" ".join(x) for x in taskopts]).split()
        log_message("...sys argv got like: %s", relevant_argv)
        
        task.options, _ = tc.parse(relevant_argv)
        log_message("...%s.options set to: %s", task, task.options)
    return None # TODO: check None has no impact on actual uptodate calc.


######################################################################
def preserve_docstrings():
    import doit.task as _t
    _t.Task._old_init_doc = _t.Task._init_doc

    def _tmp(self, doc):
        self._long_doc = doc
        return _t.Task._old_init_doc(doc)
    log_message("Patching doit.task.Task._init_doc to preserve full docstrings")
    _t.Task._init_doc = _tmp

    from doit.cmd_help import Help
    Help._old_execute = Help._execute

    def _tmp2(self, pos_args):
        res = self._old_execute(pos_args)
        task_name = pos_args[0]
        tasks = dict([(t.name, t) for t in self.task_list])
        task = tasks.get(task_name, None)
        if hasattr(task, '_long_doc') and task._long_doc is not None:
            # print only 2nd line onwards
            for line in task._long_doc.splitlines()[1::]:
                print(line)
        return res
    log_message("Patching doit.cmd_help.Help to display full docstrings")
    Help._execute = _tmp2


######################################################################
# Annoying: code below here is just about copy/pasted from doit.
# Additions marked with "pyctdev addition".

import os
import subprocess
from io import StringIO
from threading import Thread

from doit.exceptions import TaskFailed, TaskError
from doit.action import CmdAction

# TODO: decide if you want to do something about shell=True

# Identical to CmdAction.execute except for:
#   - logging the command right before running it
#   - supporting dry_run


# For logging, tried to use custom reporter instead, but it only
# reports once at start of task. (Should maybe have had only one
# action per task, but then there'd be too many tasks for a human to
# read. There are private/hidden tasks in doit, but they aren't
# shown. Need to investigate.)

class CmdAction2(CmdAction):

    dry_run = False  # pyctdev addition

    def execute(self, out=None, err=None):
        """
        Execute command action

        both stdout and stderr from the command are captured and saved
        on self.out/err. Real time output is controlled by parameters
        @param out: None - no real time output
                    a file like object (has write method)
        @param err: idem
        @return failure:
            - None: if successful
            - TaskError: If subprocess return code is greater than 125
            - TaskFailed: If subprocess return code isn't zero (and
        not greater than 125)
        """
        try:
            action = self.expand_action()
        except Exception as exc:
            return TaskError(
                "CmdAction Error creating command string", exc)

        # set environ to change output buffering
        subprocess_pkwargs = self.pkwargs.copy()
        env = None
        if 'env' in subprocess_pkwargs:
            env = subprocess_pkwargs['env']
            del subprocess_pkwargs['env']
        if self.buffering:
            if not env:
                env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'

        if self.dry_run:                                   # pyctdev addition
            log_message("Dry run; skipping: %s" % action)  # pyctdev addition
            return                                         # pyctdev addition
        log_message("Running: %s" % action)                # pyctdev addition
        
        # spawn task process
        process = subprocess.Popen(
            action,
            shell=self.shell,
            # bufsize=2, # ??? no effect use PYTHONUNBUFFERED instead
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env,
            **subprocess_pkwargs)

        output = StringIO()
        errput = StringIO()
        t_out = Thread(target=self._print_process_output,
                       args=(process, process.stdout, output, out))
        t_err = Thread(target=self._print_process_output,
                       args=(process, process.stderr, errput, err))
        t_out.start()
        t_err.start()
        t_out.join()
        t_err.join()

        self.out = output.getvalue()
        self.err = errput.getvalue()
        self.result = self.out + self.err

        # make sure process really terminated
        process.wait()

        # task error - based on:
        # http://www.gnu.org/software/bash/manual/bashref.html#Exit-Status
        # it doesnt make so much difference to return as Error or Failed anyway
        if process.returncode > 125:
            return TaskError("Command error: '%s' returned %s" %
                             (action, process.returncode))

        # task failure
        if process.returncode != 0:
            return TaskFailed("Command failed: '%s' returned %s" %
                              (action, process.returncode))

        # save stdout in values
        if self.save_out:
            self.values[self.save_out] = self.out

        log_message("Ran: %s" % action)  # pyctdev addition


# Identical to PythonAction.execute except for:
#   - logging the command right before running it
#   - read_only tasks (which can be run during dry run)

from doit.action import PythonAction, Writer


class PythonAction2(PythonAction):

    dry_run = False # pyctdev addition

    def __init__(self, py_callable, args=None,
                 kwargs=None, task=None, read_only=False): # pyctdev addition (add read_only)
        self.read_only = read_only                         # pyctdev addition
        super(
            PythonAction2,
            self).__init__(
            py_callable,
            args=args,
            kwargs=kwargs,
            task=task)

    def execute(self, out=None, err=None):
        """Execute command action

        both stdout and stderr from the command are captured and saved
        on self.out/err. Real time output is controlled by parameters
        @param out: None - no real time output
                    a file like object (has write method)
        @param err: idem

        @return failure: see CmdAction.execute
        """
        # set std stream
        old_stdout = sys.stdout
        output = StringIO()
        out_writer = Writer()
        # capture output but preserve isatty() from original stream
        out_writer.add_writer(output, old_stdout.isatty())
        if out:
            out_writer.add_writer(out)
        sys.stdout = out_writer

        old_stderr = sys.stderr
        errput = StringIO()
        err_writer = Writer()
        err_writer.add_writer(errput, old_stderr.isatty())
        if err:
            err_writer.add_writer(err)
        sys.stderr = err_writer

        kwargs = self._prepare_kwargs()

        ####################################################
        # pyctdev addition
        if self.dry_run and not self.read_only:
            log_message("Dry run; skipping: %s (%s)" % 
                        (self.py_callable.__name__,
                         self.py_callable))
            return

        log_message(
            "Calling: %s (%s)" %
            (self.py_callable.__name__,
             self.py_callable))
        ####################################################

        # execute action / callable
        try:
            returned_value = self.py_callable(*self.args, **kwargs)
        except Exception as exception:
            return TaskError("PythonAction Error", exception)
        finally:
            # restore std streams /log captured streams
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.out = output.getvalue()
            self.err = errput.getvalue()

        # if callable returns false. Task failed
        if returned_value is False:
            return TaskFailed("Python Task failed: '%s' returned %s" %
                              (self.py_callable, returned_value))
        elif returned_value is True or returned_value is None:
            pass
        elif isinstance(returned_value, str):
            self.result = returned_value
        elif isinstance(returned_value, dict):
            self.values = returned_value
            self.result = returned_value
        elif isinstance(returned_value, (TaskFailed, TaskError)):
            return returned_value
        else:
            return TaskError("Python Task error: '%s'. It must return:\n"
                             "False for failed task.\n"
                             "True, None, string or dict for successful task\n"
                             "returned %s (%s)" %
                             (self.py_callable, returned_value,
                              type(returned_value)))
