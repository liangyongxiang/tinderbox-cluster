# This file has parts from Buildbot and is modifyed by Gentoo Authors. 
# Buildbot is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members
# Origins: buildbot.steps.master.py
#           buildbot.steps.shell.py
# Modifyed by Gentoo Authors.
# Copyright 2021 Gentoo Authors

import os
import pprint
import re

from twisted.internet import defer
from twisted.internet import error
from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol
from twisted.python import runtime
from twisted.python.versions import Version

from buildbot.process import buildstep
from buildbot.process import logobserver
from buildbot.process.results import FAILURE
from buildbot.process.results import SUCCESS
from buildbot.util import deferwaiter


class MasterSetPropertyFromCommand(buildstep.ShellMixin, buildstep.BuildStep):

    """
    Run a shell command locally - on the buildmaster.  The shell command
    COMMAND is specified just as for a RemoteShellCommand.  Note that extra
    logfiles are not supported.
    """
    name = "Mastersetproperty"
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    renderables = ['command', 'env', 'property']
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, command, property=None, extract_fn=None, strip=True,
                 includeStdout=True, includeStderr=False, **kwargs):
        self.env = kwargs.pop('env', None)
        self.usePTY = kwargs.pop('usePTY', 0)
        self.interruptSignal = kwargs.pop('interruptSignal', 'KILL')
        self.logEnviron = kwargs.pop('logEnviron', True)

        self.property = property
        self.extract_fn = extract_fn
        self.strip = strip
        self.includeStdout = includeStdout
        self.includeStderr = includeStderr
        
        if not ((property is not None) ^ (extract_fn is not None)):
            config.error(
                "Exactly one of property and extract_fn must be set")

        super().__init__(**kwargs)

        self.command = command
        self.masterWorkdir = self.workdir
        self._deferwaiter = deferwaiter.DeferWaiter()
        self._status_object = None
        self.success = True

        if self.extract_fn:
            self.includeStderr = True

        self.observer = logobserver.BufferLogObserver(
            wantStdout=self.includeStdout,
            wantStderr=self.includeStderr)
        self.addLogObserver('stdio', self.observer)

    class LocalPP(ProcessProtocol):

        def __init__(self, step):
            self.step = step
            self._finish_d = defer.Deferred()
            self.step._deferwaiter.add(self._finish_d)

        def outReceived(self, data):
            self.step._deferwaiter.add(self.step.stdio_log.addStdout(data))

        def errReceived(self, data):
            self.step._deferwaiter.add(self.step.stdio_log.addStderr(data))

        def processEnded(self, status_object):
            if status_object.value.exitCode is not None:
                msg = "exit status {}\n".format(status_object.value.exitCode)
                self.step._deferwaiter.add(self.step.stdio_log.addHeader(msg))

            if status_object.value.signal is not None:
                msg = "signal {}\n".format(status_object.value.signal)
                self.step._deferwaiter.add(self.step.stdio_log.addHeader(msg))

            self.step._status_object = status_object
            self._finish_d.callback(None)

    @defer.inlineCallbacks
    def run(self):
        # render properties
        command = self.command
        # set up argv
        if isinstance(command, (str, bytes)):
            if runtime.platformType == 'win32':
                # allow %COMSPEC% to have args
                argv = os.environ['COMSPEC'].split()
                if '/c' not in argv:
                    argv += ['/c']
                argv += [command]
            else:
                # for posix, use /bin/sh. for other non-posix, well, doesn't
                # hurt to try
                argv = ['/bin/sh', '-c', command]
        else:
            if runtime.platformType == 'win32':
                # allow %COMSPEC% to have args
                argv = os.environ['COMSPEC'].split()
                if '/c' not in argv:
                    argv += ['/c']
                argv += list(command)
            else:
                argv = command

        self.stdio_log = yield self.addLog("stdio")

        if isinstance(command, (str, bytes)):
            yield self.stdio_log.addHeader(command.strip() + "\n\n")
        else:
            yield self.stdio_log.addHeader(" ".join(command) + "\n\n")
        yield self.stdio_log.addHeader("** RUNNING ON BUILDMASTER **\n")
        yield self.stdio_log.addHeader(" in dir {}\n".format(os.getcwd()))
        yield self.stdio_log.addHeader(" argv: {}\n".format(argv))

        if self.env is None:
            env = os.environ
        else:
            assert isinstance(self.env, dict)
            env = self.env
            for key, v in self.env.items():
                if isinstance(v, list):
                    # Need to do os.pathsep translation.  We could either do that
                    # by replacing all incoming ':'s with os.pathsep, or by
                    # accepting lists.  I like lists better.
                    # If it's not a string, treat it as a sequence to be
                    # turned in to a string.
                    self.env[key] = os.pathsep.join(self.env[key])

            # do substitution on variable values matching pattern: ${name}
            p = re.compile(r'\${([0-9a-zA-Z_]*)}')

            def subst(match):
                return os.environ.get(match.group(1), "")
            newenv = {}
            for key, v in env.items():
                if v is not None:
                    if not isinstance(v, (str, bytes)):
                        raise RuntimeError(("'env' values must be strings or "
                                            "lists; key '{}' is incorrect").format(key))
                    newenv[key] = p.sub(subst, env[key])
            env = newenv

        if self.logEnviron:
            yield self.stdio_log.addHeader(" env: %r\n" % (env,))

        # TODO add a timeout?
        self.process = reactor.spawnProcess(self.LocalPP(self), argv[0], argv,
                                            path=self.masterWorkdir, usePTY=self.usePTY, env=env)

        # self._deferwaiter will yield only after LocalPP finishes

        yield self._deferwaiter.wait()
        status_value = self._status_object.value
        if status_value.signal is not None:
            self.descriptionDone = ["killed ({})".format(status_value.signal)]
            self.success = False
        elif status_value.exitCode != 0:
            self.descriptionDone = ["failed ({})".format(status_value.exitCode)]
            self.success = False
            

        yield self.stdio_log.finish()

        property_changes = {}

        if self.property:
            if not self.success:
                return FAILURE
            result = self.observer.getStdout()
            if self.strip:
                result = result.strip()
            propname = self.property
            self.setProperty(propname, result, "MastertSetPropertyFromCommand Step")
            property_changes[propname] = result
        else:
            new_props = self.extract_fn(self._status_object.value.exitCode,
                                        self.observer.getStdout(),
                                        self.observer.getStderr())
            for k, v in new_props.items():
                self.setProperty(k, v, "MasterSetPropertyFromCommand Step")
            property_changes = new_props

        props_set = ["{}: {}".format(k, repr(v))
                     for k, v in sorted(property_changes.items())]
        yield self.addCompleteLog('property changes', "\n".join(props_set))

        if len(property_changes) > 1:
            self.descriptionDone = '{} properties set'.format(len(property_changes))
        elif len(property_changes) == 1:
            self.descriptionDone = 'property \'{}\' set'.format(list(property_changes)[0])
        if not self.success:
            return FAILURE
        return SUCCESS

    def interrupt(self, reason):
        try:
            self.process.signalProcess(self.interruptSignal)
        except KeyError:  # Process not started yet
            pass
        except error.ProcessExitedAlready:
            pass
        super().interrupt(reason)
