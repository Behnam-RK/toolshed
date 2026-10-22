# Linear

Tools come from the official Linear plugin (`linear@claude-plugins-official`).
Without them, dabir drafts locally, says publishing needs that plugin, and
stops before step 6.

## Read

| Need | Tool |
|---|---|
| Project, milestones | `get_project` (`includeMilestones`) |
| Issues | `list_issues` (`project`) |
| Existing shaping docs | `list_documents` (`projectId`), then `get_document` |
| Comment threads on a version | `list_comments` (`documentId`) |
| Author for the header | `get_user` (`me`) |

Page through every comment (`cursor` while `hasNextPage`). Group replies
under their root (`parentId: null`); a thread's later replies often settle it
already, so answer the thread's final position, not its first comment. Read
inline comments (`quotedText` set) too and quote the anchored text in
Appendix A. Comments may be in any language; Appendix A gives their gist in
the doc's language.

## Publish

- **Title:** `<Project> — Shaping vN`. The first version is v1. A revision is
  the highest existing version plus one (an unnumbered title counts as v1).
- **Create** with `save_document`: `title`, `project`, `content`. A version is
  always a new document; never update an earlier one.
- **Supersedes** in the header links the previous version's URL.
- Keep markdown plain: simple tables (no merged cells, no HTML), images as
  links unless the user uploads them. Never copy Linear's own tags
  (`<linear-image>`, `<pull-request>`) from a previous version; link the URL.

## After publishing (each on its own yes)

- **Replies:** `save_comment` with `parentId` set to each thread's root on the
  previous version: one line pointing to vN and, when it changed, the row in
  Appendix A. Never resolve or delete threads.
- **Issues:** `save_issue` with the project's team and `project`; title from
  the `Missing:` item or the Open decision; assignee only when the doc names
  an owner. Link the doc in the description.
