import os
import subprocess
import unittest
from test.setup_test import SetupTest


class TestSampleRule(unittest.TestCase):

    def check_run_hook(self, hook_script, test_env, expected_rc):
        self.assertTrue(os.path.isfile(hook_script))

        process = subprocess.Popen(hook_script, env=test_env, stdout=subprocess.PIPE)
        streamdata = process.communicate()[0]
        rc = process.returncode

        if rc != expected_rc:
            for line in streamdata.splitlines():
                print(line)
        self.assertEqual(rc, expected_rc)

    def get_def_github(self):
        def_env = os.environ.copy()
        def_env['GITHOOK_DEBUG'] = '1'
        def_env['GITHOOK_PREPUSH_REMOTE'] = 'github'
        def_env['GITHOOK_PREPUSH_URL'] = 'https://github.com/xxxx/prend.git'
        def_env['GITHOOK_PREPUSH_LOCAL_REF'] = 'refs/heads/master'
        def_env['GITHOOK_PREPUSH_LOCAL_SHA'] = '96923b8365375c4275f2f4044039f2b3ee81b930'
        def_env['GITHOOK_PREPUSH_REMOTE_REF'] = 'refs/heads/master'
        def_env['GITHOOK_PREPUSH_REMOTE_SHA'] = 'ce05260dda09363ea3ade1339cc1f476ee2765b9'
        return def_env

    def get_def_other(self):
        def_env = self.get_def_github()
        def_env['GITHOOK_PREPUSH_REMOTE'] = 'other'
        def_env['GITHOOK_PREPUSH_URL'] = 'https://other.com/xxxx/prend.git'
        return def_env

    def test_pre_push_prevent_private(self):

        hook_script = os.path.join(SetupTest.get_project_dir(), 'tools', 'githooks', 'pre-push-pervent-private.sh')

        test_env = self.get_def_github()
        self.check_run_hook(hook_script, test_env, 0)

        test_env = self.get_def_github()
        test_env['GITHOOK_PREPUSH_LOCAL_REF'] = 'refs/heads/priVate'
        self.check_run_hook(hook_script, test_env, 1)

        test_env = self.get_def_github()
        test_env['GITHOOK_PREPUSH_REMOTE_REF'] = 'refs/heads/privatE/gggg'
        self.check_run_hook(hook_script, test_env, 1)

        test_env = self.get_def_other()
        test_env['GITHOOK_PREPUSH_LOCAL_REF'] = 'refs/heads/private'
        test_env['GITHOOK_PREPUSH_REMOTE_REF'] = 'refs/heads/private'
        self.check_run_hook(hook_script, test_env, 0)

