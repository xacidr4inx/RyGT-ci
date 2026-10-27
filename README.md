# RyGT GitLab Windows workers

This repository hosts only the Windows runner workflow for
https://gitlab.com/rygt-team/RyGT. GitLab remains the source of truth and the
pipeline/package dashboard. Requests build an exact public GitLab commit;
no GitLab credentials or game data are copied here.

GitLab dispatches the workflow, waits for it, verifies the source revision and
checksums, and exposes the returned files as GitLab pipeline artifacts. The
workflow has read-only repository permissions and uses pinned official actions.
