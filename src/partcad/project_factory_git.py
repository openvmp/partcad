#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

from git import Repo
import os
import hashlib

from . import project_factory as pf


class GitImportConfiguration:
    def __init__(self):
        self.import_config_url = self.config_obj.get("url")
        self.import_rel_path = self.config_obj.get("relPath")


class ProjectFactoryGit(pf.ProjectFactory, GitImportConfiguration):
    def __init__(self, ctx, parent, config, name=None):
        pf.ProjectFactory.__init__(self, ctx, parent, config, name)
        GitImportConfiguration.__init__(self)

        # TODO(clairbee): Clone self.import_config_url to self.cache_path
        self.cache_path = self._clone_or_update_repo(self.import_config_url)

        # Complement the config object here if necessary
        self.path = self.cache_path
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
        cache_path = os.path.join(cache_dir, repo_hash)

        # Check if the repository is already cached.
        if os.path.exists(cache_path):
            try:
                # Try to open the existing repository and update it.
                repo = Repo(cache_path)
                origin = repo.remote("origin")
                origin.pull()
                repo.head.checkout(origin.head.name, force=True)
                return cache_path
            except Exception:
                # If update fails, fall back to cloning a new copy.
                pass
        else:
            # Clone the repository if not cached.
            try:
                Repo.clone_from(repo_url, cache_path)
            except Exception as e:
                raise RuntimeError(f"Failed to clone repository: {e}")

        if not self.import_rel_path is None:
            cache_path = os.path.join(cache_path, self.import_rel_path)

        return cache_path
