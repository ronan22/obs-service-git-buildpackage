# vim:fileencoding=utf-8:et:ts=4:sw=4:sts=4
#
# Copyright (C) 2013 Intel Corporation <markus.lehtonen@linux.intel.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
"""Tests for the git-buildpackage OBS source service"""

import os
from nose.tools import assert_raises # pylint: disable=E0611

from obs_service_gbp.command import main as service
from tests import UnitTestsBase


class TestService(UnitTestsBase):
    """Base class for unit tests"""

    def _check_files(self, files, directory=''):
        """Check that the tmpdir content matches expectations"""
        found = set(os.listdir(os.path.join(self.tmpdir, directory)))
        expect = set(files)
        assert found == expect, "Expected: %s, Found: %s" % (expect, found)

    def test_invalid_options(self):
        """Test invalid options"""
        # Non-existing option
        with assert_raises(SystemExit):
            service(['--foo'])
        # Option without argument
        with assert_raises(SystemExit):
            assert service(['--url'])
        # Invalid repo
        assert service(['--url=foo/bar.git']) != 0

    def test_basic_rpm_export(self):
        """Test that rpm export works"""
        assert service(['--url', self.orig_repo.path, '--revision=rpm']) == 0
        self._check_files(['test-package.spec', 'test-package_0.1.tar.gz'])

    def test_basic_deb_export(self):
        """Test that deb export works"""
        assert service(['--url', self.orig_repo.path, '--revision=deb']) == 0
        self._check_files(['test-package_0.1.dsc', 'test-package_0.1.tar.gz'])

    def test_empty_export(self):
        """Test case where nothing is exported"""
        assert service(['--url', self.orig_repo.path, '--revision=source']) == 0
        self._check_files([])
        assert service(['--url', self.orig_repo.path, '--rpm=no',
                       '--deb=no']) == 0
        self._check_files([])

    def test_basic_dual_export(self):
        """Test that simultaneous rpm and deb export works"""
        assert service(['--url', self.orig_repo.path]) == 0
        self._check_files(['test-package.spec', 'test-package_0.1.dsc',
                           'test-package_0.1.tar.gz'])

    def test_gbp_rpm_failure(self):
        """Test git-buildpackage-rpm failure"""
        assert service(['--url', self.orig_repo.path, '--outdir=foo/bar']) == 2
        assert service(['--url', self.orig_repo.path, '--rpm=yes',
                        '--revision=source']) == 2

    def test_gbp_deb_failure(self):
        """Test git-buildpackage (deb) failure"""
        assert service(['--url', self.orig_repo.path, '--rpm=no',
                        '--outdir=foo/bar']) == 3
        assert service(['--url', self.orig_repo.path, '--deb=yes',
                        '--revision=source']) == 3

    def test_options_outdir(self):
        """Test the --outdir option"""
        outdir = os.path.join(self.tmpdir, 'outdir')
        args = ['--url', self.orig_repo.path, '--outdir=%s' % outdir]
        assert service(args) == 0
        self._check_files(['test-package.spec', 'test-package_0.1.dsc',
                           'test-package_0.1.tar.gz'], outdir)

    def test_options_revision(self):
        """Test the --revision option"""
        assert service(['--url', self.orig_repo.path, '--revision=master']) == 0
        self._check_files(['test-package.spec', 'test-package_0.1.dsc',
                           'test-package_0.1.tar.gz'])
        assert service(['--url', self.orig_repo.path, '--revision=foobar']) == 1

    def test_options_verbose(self):
        """Test the --verbose option"""
        assert service(['--url', self.orig_repo.path, '--verbose=yes']) == 0
        with assert_raises(SystemExit):
            service(['--url', self.orig_repo.path, '--verbose=foob'])

    def test_options_spec_vcs_tag(self):
        """Test the --spec-vcs-tag option"""
        assert service(['--url', self.orig_repo.path,
                        '--spec-vcs-tag=orig/%(tagname)s']) == 0

    def test_options_config(self):
        """Test the --config option"""
        # Create config file
        with open('my.conf', 'w') as conf:
            conf.write('[general]\n')
            conf.write('repo-cache-dir = my-repo-cache\n')

        # Mangle environment
        default_cache = os.environ['OBS_GIT_BUILDPACKAGE_REPO_CACHE_DIR']
        del os.environ['OBS_GIT_BUILDPACKAGE_REPO_CACHE_DIR']

        # Check that the repo cache we configured is actually used
        assert (service(['--url', self.orig_repo.path, '--config', 'my.conf'])
                == 0)
        assert not os.path.exists(default_cache), os.listdir('.')
        assert os.path.exists('my-repo-cache'), os.listdir('.')

