# claude-plugins

Personal Claude Code marketplace: upstream plugins rebuilt weekly with small
patches (`patches/<name>.sh`), versioned `<upstream>+<sha>` so auto-update
picks up every upstream change. A patch that stops applying fails the
`sync upstreams` workflow and opens an issue.

```
/plugin marketplace add Behnam-RK/claude-plugins
```

Upstream licenses are kept in each `plugins/<name>/` (MIT, Elastic-2.0).
