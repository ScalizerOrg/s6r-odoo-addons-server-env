# Copyright 2018 Camptocamp (https://www.camptocamp.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)


import os
from unittest.mock import patch

from odoo.tools.config import config as odoo_config

from odoo.addons.server_environment import server_env

from .common import ServerEnvironmentCase


class TestRunningEnvDefault(ServerEnvironmentCase):
    def test_running_env_default(self):
        """When no running_env is configured and no RUNNING_ENV/ODOO_STAGE
        env var is set, it defaults to `test`.

        ``_load_running_env()`` only runs once, at import time, so by the
        time this test executes, ``odoo_config["running_env"]`` may already
        be pinned to whatever the real process environment provided (e.g.
        "dev" on an odoo.sh dev branch) — asserting on it directly couples
        the test to wherever it happens to run. Clear both the config value
        and the env vars, then re-run the resolution in isolation so the
        test verifies the actual default logic instead.
        """
        with patch.dict(odoo_config.options, clear=False), patch.dict(
            os.environ, clear=False
        ):
            odoo_config.options.pop("running_env", None)
            os.environ.pop("RUNNING_ENV", None)
            os.environ.pop("ODOO_STAGE", None)
            server_env._load_running_env()
            self.assertEqual(odoo_config["running_env"], "test")


@patch.dict(odoo_config.options, {"running_env": "testing"})
class TestEnvironmentVariables(ServerEnvironmentCase):
    def test_env_variables(self):
        public = "[section]\n" "foo=bar\n" "bar=baz\n"
        secret = "[section]\n" "bar=foo\n" "alice=bob\n"
        with self.set_config_dir(None), self.set_env_variables(public, secret):
            parser = server_env._load_config()
            self.assertEqual(list(parser.keys()), ["DEFAULT", "section"])
            self.assertDictEqual(
                dict(parser["section"].items()),
                {"alice": "bob", "bar": "foo", "foo": "bar"},
            )

    def test_env_variables_override(self):
        public = "[external_service.ftp]\n" "user=foo\n"
        with self.set_config_dir("testfiles"), self.set_env_variables(public):
            parser = server_env._load_config()
            val = parser.get("external_service.ftp", "user")
            self.assertEqual(val, "foo")
