"""pyctdev application

Load pyctdev's tasks and then any project-specific ones.

Also apply various hacks to doit (e.g. making full docstrings
available).
"""

import sys
import os
import tempfile

import doit
import doit.loader
from doit.doit_cmd import DoitMain
from doit.cmd_base import DodoTaskLoader
from doit.exceptions import InvalidDodoFile

from .util import log_message, get_role
from . import _doithacks

_doithacks.preserve_docstrings()


class PyctdevLoader(DodoTaskLoader):

    def load_tasks(self, cmd, params, args):
        """
        Load pyctdev and user-defined tasks and config.

          * loads tasks from 'univeral' ecosystem and globally selected
            ecosystem

          * supplies a default DOIT_CONFIG

          * loads tasks and config from dodo.py (later tasks & options
            replace earlier ones).
        """
        role = get_role()

        default_DOIT_CONFIG = {
            'verbosity': 2 if role=='user' else 3,
            'backend': 'sqlite3',
        }

        tasks = []

        # TODO: simplify this

        # Note: only supports one ecosystem at a time for now

        log_message("Determining ecosystem...")
        ecosystem = doit.get_var("ecosystem")
        # TODO: might need to restore hack for older doit?
        if ecosystem is None:
            log_message("...not specified at command line")
            ecosystem = os.getenv("PYCTDEV_ECOSYSTEM")
            if ecosystem is None:
                log_message("...not specified as PYCTDEV_ECOSYSTEM env var")
            else:
                log_message("...found PYCTDEV_ECOSYSTEM=%s", ecosystem)
        else:
            log_message("...ecosystem=%s supplied at command line", ecosystem)

        # TODO: maybe don't do this?
        if ecosystem is None:
            ecosystem = 'pip'
            log_message("...defaulting to ecosystem=pip")

        # TODO: consider some kind of plugins dir?
        import pyctdev.tasks.universal
        # TODO at least use importlib or whatever it is
        exec("import pyctdev.tasks.%s" % ecosystem)

        task_fns = pyctdev.tasks.get_tasks(ecosystem)

        tasks, config = self._load_from(cmd, task_fns, self.cmd_names)
        assert len(config) == 0
        config = default_DOIT_CONFIG

        try:
            dodo_module = doit.loader.get_module(
                params['dodoFile'],
                params['cwdPath'],
                params['seek_file'])
        except (TypeError, InvalidDodoFile):  # actually it's missing dodo file here
            dodo_module = None

        if dodo_module:
            log_message(
                "Reading local tasks and config from %s",
                dodo_module.__file__)
            dodo_tasks, dodo_config = self._load_from(
                cmd, dodo_module, self.cmd_names)

            for key, val in dodo_config.items():
                if key in config:
                    log_message(
                        "Overriding default config %s=%s with %s",
                        key,
                        config[key],
                        val)
                config[key] = val

            # tasks go in order they're defined, and later ones replace earlier
            existing_task_names = {task.name: task for task in tasks}
            for dodo_task in dodo_tasks:
                if dodo_task.name in existing_task_names:
                    log_message(
                        "Replacing default task '%s' with version from %s",
                        dodo_task.name,
                        dodo_module.__file__)
                    tasks.remove(existing_task_names[dodo_task.name])
                    tasks.append(dodo_task)
        else:
            log_message("dodo.py file not found (optional)")

        _doithacks.update_all_params(tasks)

        return tasks, config


def main():
    # TODO: most of below is hack to support --dry-run (including
    # switch out db during a dry run)
    tmpdb = None
    if '--dry-run' in sys.argv:
        _doithacks.CmdAction2.dry_run = _doithacks.PythonAction2.dry_run = True
        tmpdb = tempfile.NamedTemporaryFile(delete=False)
        tmpdb.close()
        log_message(
            "--dry-run specified; using temporary file %s for doit db",
            tmpdb.name)
        sys.argv[sys.argv.index('--dry-run')] = '--db-file=%s' % tmpdb.name

    try:
        sys.exit(DoitMain(PyctdevLoader()).run(sys.argv[1:]))
    finally:
        if tmpdb is not None:
            os.unlink(tmpdb.name)


if __name__ == "__main__":
    main()