# Copyright (c) 2016 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the --interactive option to the  'import' command"""

import os
import subprocess

import mock
from testscenarios import TestWithScenarios
from testtools.content import text_content
from testtools.matchers import Equals

from git_upstream.lib.pygitcompat import Commit
from git_upstream import main
from git_upstream.tests.base import BaseTestCase
from git_upstream.tests.base import get_scenarios


@mock.patch.dict('os.environ', {'GIT_SEQUENCE_EDITOR': 'cat'})
class TestImportInteractiveCommand(TestWithScenarios, BaseTestCase):

    commands, parser = main.build_parsers()
    scenarios = get_scenarios(os.path.join(os.path.dirname(__file__),
                              "interactive_scenarios"))

    def setUp(self):
        # add description in case parent setup fails.
        self.addDetail('description', text_content(self.desc))

        script_cmdline = self.parser.get_default('script_cmdline')
        script_cmdline[-1] = os.path.join(os.getcwd(), script_cmdline[-1])
        self.parser.set_defaults(script_cmdline=script_cmdline)

        # builds the tree to be tested
        super(TestImportInteractiveCommand, self).setUp()

    def test_interactive(self):
        upstream_branch = self.branches['upstream'][0]
        target_branch = self.branches['head'][0]

        cmdline = self.parser.get_default('script_cmdline') + self.parser_args
        subprocess.check_output(cmdline, stderr=subprocess.STDOUT)

        expected = getattr(self, 'expect_rebased', [])
        if expected:
            changes = list(Commit.iter_items(
                self.repo, '%s..%s^2' % (upstream_branch, target_branch)))
            self.assertThat(
                len(changes), Equals(len(expected)),
                "should only have seen %s changes, got: %s" %
                (len(expected),
                 ", ".join(["%s:%s" % (commit.hexsha,
                                       commit.message.splitlines()[0])
                           for commit in changes])))

            # expected should be listed in order from oldest to newest, so
            # reverse changes to match as it would be newest to oldest.
            changes.reverse()
            for commit, node in zip(changes, expected):
                subject = commit.message.splitlines()[0]
                node_subject = self._graph[node].message.splitlines()[0]
                self.assertThat(subject, Equals(node_subject),
                                "subject '%s' of commit '%s' does not match "
                                "subject '%s' of node '%s'" % (
                                    subject, commit.hexsha, node_subject,
                                    node))
