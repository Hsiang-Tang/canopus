# Git identity, remote, and commit rules

## Identity

- Configure identity per repository (`git config user.name` / `user.email` in
  that repository), never by changing the global identity for one project.
- Personal and public repositories use the owner's declared identity. A public
  repository should use the hosting provider's noreply address.
- Employer-owned repositories use the employer-provided identity only. A
  personal identity or exception never carries over.
- When the workspace manifest declares an expected email for a repository,
  `tools/workspace_doctor.py` reports any mismatch as an error.

## AI attribution

- Each repository declares its attribution policy in its `AGENTS.md`: either
  no AI trailers, or one `Co-authored-by:` trailer per AI tool that materially
  authored the committed result.
- Review-only assistance never claims co-authorship.
- Employer-owned repositories follow their own documented commit convention
  exactly. Add no AI trailer or session link unless that convention asks for
  one, regardless of which agent commits.
- Apply the policy going forward. Do not rewrite history to add or remove
  attribution.

## Remotes

- The target project's remote policy decides where it may push: a named host
  and URL-prefix allowlist, a required remote, or no remote at all.
- Local-only projects receive no hosted remote. Private hosting is not an
  automatic exception.
- Employer work uses only the employer-approved remote. Never guess a remote or
  mirror employer work to a personal host. With no approved remote, commit
  locally and wait for the exact URL.
- Every fetch and push URL must stay inside the declared allowlist; the
  workspace doctor checks this.

## Verify hosting before the first push

Before the first push, a remote change, or newly hosting history that contains
private material:

1. Resolve the exact owner, remote URL, and target branch without uploading.
2. Query the provider: confirm visibility, the expected owner, only approved
   collaborators, and that public-serving features (such as static pages) are
   disabled when applicable.
3. Confirm the project's remote policy permits that exact destination.
4. Push, then query again: controls unchanged, the intended commit on the
   intended branch.

Stop without pushing when any value cannot be verified or is unexpected.
Private hosting is access control, not encryption, and not permission to move
employer or restricted material.

If private data is already in history, deleting the files does not make the
history publishable. Build a public version as a separately reviewed,
sanitized export with new history.

## Branches

- Do not commit directly to the default branch for R2 or R3 work. Branch first.
- Branch names: `<kind>/<lowercase-kebab-topic>` where kind is one of
  `feature`, `fix`, `docs`, `rules`, `knowledge`, `playbooks`, or a
  project-declared prefix.
- Parallel writers each get their own branch and worktree (`workstreams.md`).
  Two writers never share a branch.

## Commits

- Inspect staged paths and the staged diff before every commit. This is agent
  verification, not a request for owner confirmation.
- One concern per commit. Never mix unrelated projects or nested repositories.
- The subject says what changed in the imperative mood. The body says why when
  it is not obvious.
- Never commit secrets, `.env` files, machine-local manifests, absolute local
  paths, logs, transcripts, caches, databases, or build output.
- Before committing to a public repository, run
  `python3 tools/audit_publication.py` with any source-specific `--deny`
  terms, and `git diff --cached --check`.

## Authority

- An explicit change, fix, or finish request authorizes routine commits and
  pushes to the already-confirmed remote for that task.
- Specific owner authority is required to add or change a remote, change
  repository visibility, publish a release or package, force-push, or rewrite
  shared history.
- Never force-push a shared branch. Recover with a revert.

## Review queue resolution

When the owner asks to clear an authorized private review queue, or the agent
opened a pull request as part of an authorized delivery chain, the agent may
review, repair on a follow-up branch, wait for checks, merge, verify the
default branch, and close the linked Issue. Before an agent-owned merge, all of
these must hold:

- the repository and remote are authorized, the pull request is not a draft,
  and every commit uses the accepted identity;
- the diff matches its Issue or spec and its information boundary; required
  checks pass; no requested change or unresolved thread remains;
- rule or knowledge candidates passed their required boundary review;
- the change creates no new public exposure and no financial, legal, account,
  credential, or irreversible external decision;
- rollback is available through revert or an accepted recovery path.

Green CI is necessary, not sufficient. When a candidate fails a gate, fix it
and rerun the evidence. Prefer one active pull request per outcome; close
superseded ones with a comment saying why.

## Cleanup

- Delete a merged branch only after the merge is verified on the remote
  default branch.
- Remove a worktree only after its branch is merged or explicitly abandoned
  with a recorded resume point.
- Never delete an unmerged branch as part of another session's takeover.
