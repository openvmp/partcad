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
import logging
import os

from . import project_factory as pf


class GitImportConfiguration:
    def __init__(self):
        self.import_config_url = self.config_obj.get("url")
        self.import_revision = self.config_obj.get("revision")
        self.import_rel_path = self.config_obj.get("relPath")


class ProjectFactoryGit(pf.ProjectFactory, GitImportConfiguration):
    def __init__(self, ctx, parent, config, name=None):
        pf.ProjectFactory.__init__(self, ctx, parent, config, name)
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
            cache_dir = os.getenv("HOME", "/tmp") + "/.partcad/git"

        # Generate a unique identifier for the repository based on its URL.
        repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()
        if self.import_revision is not None:
            repo_hash += "-" + self.import_revision
        cache_path = os.path.join(cache_dir, repo_hash)

        # Check if the repository is already cached.
        if os.path.exists(cache_path):
            try:
                # Try to open the existing repository and update it.
                repo = Repo(cache_path)
                origin = repo.remote("origin")
                before = repo.active_branch.commit
                if self.import_revision is None:
                    origin.pull()
                else:
                    origin.fetch()
                    repo.git.checkout(self.import_revision, force=True)
                after = repo.active_branch.commit
                if before != after:
                    logging.info("\nUpdated the GIT repo: %s" % self.import_config_url)
            except Exception as e:
                logging.error("\nException: %s" % e)
                # If update fails, fall back to cloning a new copy.
                pass
        else:
            # Clone the repository if not cached.
            try:
                logging.info("\nCloning the GIT repo: %s" % self.import_config_url)
                Repo.clone_from(repo_url, cache_path)
            except Exception as e:
                raise RuntimeError(f"Failed to clone repository: {e}")

        if not self.import_rel_path is None:
            cache_path = os.path.join(cache_path, self.import_rel_path)

        return cache_path
