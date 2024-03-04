#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

from git import Repo
import hashlib
import os
import pathlib
import time

from . import project_factory as pf
from . import logging as pc_logging
from .user_config import user_config


class GitImportConfiguration:
    def __init__(self):
        self.import_config_url = self.config_obj.get("url")
        self.import_revision = self.config_obj.get("revision")
        self.import_rel_path = self.config_obj.get("relPath")


class ProjectFactoryGit(pf.ProjectFactory, GitImportConfiguration):
    def __init__(self, ctx, parent, config):
        pf.ProjectFactory.__init__(self, ctx, parent, config)
        GitImportConfiguration.__init__(self)

        self.path = self._clone_or_update_repo(self.import_config_url)

        # Complement the config object here if necessary
        self._create(config)

        # TODO(clairbee): actually fill in the self.project object here

        self._save()

    def _clone_or_update_repo(self, repo_url, cache_dir=None):
        """
        Clones a Git repository to a local directory and keeps it up-to-date.

        Args:
          repo_url: URL of the Git repository to clone.
          cache_dir: Directory to store the cached copies of repositories (defaults to ".cache").

        Returns:
          Local path to the cloned repository.
        """

        if cache_dir is None:
            cache_dir = os.path.join(user_config.internal_state_dir, "git")

        # Generate a unique identifier for the repository based on its URL.
        repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()
        if self.import_revision is not None:
            repo_hash += "-" + self.import_revision
        cache_path = os.path.join(cache_dir, repo_hash)
        guard_path = os.path.join(cache_path, ".partcad.git.cloned")

        # Check if the repository is already cached.
        if os.path.exists(cache_path):
            try:
                before = None

                # Try to open the existing repository and update it.
                if self.import_revision is None:
                    if user_config.force_update or (
                        time.time() - os.path.getmtime(guard_path) > 24 * 3600
                    ):
                        repo = Repo(cache_path)
                        origin = repo.remote("origin")
                        before = repo.active_branch.commit
                        origin.pull()
                        pathlib.Path(guard_path).touch()
                else:
                    repo = Repo(cache_path)
                    origin = repo.remote("origin")
                    before = repo.active_branch.commit
                    if user_config.force_update or (
                        before != self.import_revision
                        or (
                            time.time() - os.path.getmtime(guard_path)
                            > 24 * 3600
                        )
                    ):
                        # Need to check for updates
                        origin.fetch()
                        repo.git.checkout(self.import_revision, force=True)
                        pathlib.Path(guard_path).touch()

                if not before is None:
                    # Update was performed
                    after = repo.active_branch.commit
                    if before != after:
                        pc_logging.info(
                            "Updated the GIT repo: %s" % self.import_config_url
                        )
            except Exception as e:
                pc_logging.error("Exception: %s" % e)
                # Fall back to using the previous copy
        else:
            # Clone the repository if not cached.
            try:
                pc_logging.info(
                    "Cloning the GIT repo: %s" % self.import_config_url
                )
                repo = Repo.clone_from(repo_url, cache_path)
                if not self.import_revision is None:
                    repo.git.checkout(self.import_revision, force=True)

                if not os.path.exists(guard_path):
                    pathlib.Path(guard_path).touch()
            except Exception as e:
                raise RuntimeError(f"Failed to clone repository: {e}")

        if not self.import_rel_path is None:
            cache_path = os.path.join(cache_path, self.import_rel_path)

        return cache_path
