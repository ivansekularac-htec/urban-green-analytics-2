# Contributing

How our team builds the platform together. Read this on day one and refer back at every sprint boundary.


## TL;DR

- All interns, one central repo. Everyone builds every task on their own branch.
- Merges happen **per epic** at the end of each sprint. Only one canonical PR wins per epic.
- Mentor decides; peer review feeds the decision.
- At the sprint boundary every branch hard-resets to the merged `main`. Next sprint, everyone builds on the canonical platform, not on their own version.

## Branch model

- `main` is canonical and protected. Only the mentor merges.
- Each intern works on `intern/<name>/<module>` for the duration of the sprint. Example: `intern/alice/m2-streaming`.
- Cut short-lived feature branches off your sprint branch for each epic PR: `intern/alice/m2-kafka-broker`. PRs are opened from the feature branch into `main`.
- All PRs target `main`. Not your sprint branch, not someone else's branch. This is what makes cross-intern peer review possible.
- All merges to `main` are squash-merges. Canonical history reads as one commit per epic per sprint.

### Branch naming

```
intern/<name>/<module>            # sprint integration branch
intern/<name>/<module>-<topic>    # epic feature branch (PR source)
```

Use lowercase. Pick a stable `<name>` (first name or GitHub handle) and stick with it for all 8 sprints.

## Sprint cadence


| Day | What happens |
|---|---|
| 1 | **Sprint kickoff.** Mentor walks the module's epics. You cut your sprint branch from `main`. |
| 1 - 9 | **Build.** Open PRs as epics finish. First PRs typically arrive day 5 - 7. |
| 10 - 12 | **Review window.** Each PR needs a peer review and a mentor review before the merge contest closes. |
| 12 - 13 | **Merge contest.** Mentor selects the canonical PR per epic, squash-merges, and leaves a rationale comment on every non-merged PR. |
| 13 | **Sprint demo.** Designated presenter walks the merged build end-to-end. |
| 14 | **Retro + reset.** Everyone hard-resets their next-sprint branch to `main`. |

The cadence is back-loaded on purpose. PRs queue and get reviewed during the sprint; only at the boundary does the strongest one win per epic. Don't expect to be merged the day you open.

## Opening a PR

One PR per epic. Title format:

```
[<EPIC-KEY>] <short summary>
```

The PR template (`.github/PR_TEMPLATE.md`) requires:

- The Jira epic key (one PR = one epic).
- The acceptance-criteria checklist for the epic. Tick the boxes you've satisfied.
- A reproducible verification recipe (commands a reviewer can run on a fresh checkout).
- Evidence: terminal output, dashboard screenshots, query results, whatever proves it works.
- An @-mention of your assigned peer reviewer.
- Optional notes to the mentor for the merge contest.

CI must pass before the merge contest. Each module's epics include the CI gates for the services that module ships, so if you're touching a service you're also responsible for keeping its workflow green.

## Reviewing PRs

The pairing rotates so every intern reviews every other intern over the program.

What a useful review does:

- Confirms each acceptance-criteria box can be reproduced from the verification recipe.
- Calls out design choices worth discussing - not nits, not formatting (linters handle that).
- Points to specific lines, not vague impressions.
- Asks questions when something isn't clear; an unclear PR is signal for the mentor too.

Reviews don't gate merge - the mentor's contest call is final - but they shape the call and they're the main way you teach yourself by reading other people's code. Skipping a review you were assigned shows up in retro.

## Reset protocol

Day 14 of every sprint, after demo and retro:

```bash
git fetch origin
git checkout -b intern/<name>/<next-module> origin/main
git push -u origin intern/<name>/<next-module>
```

Your previous sprint branch stays in the repo as a personal record. You are **not** rebasing your own code forward - the canonical version is now `main`, and the next sprint you build on top of `main`, not on top of your own work.

Yes, this can sting if you spent two weeks on a build that didn't merge. The value was the build itself plus the review feedback, not in shipping your version forward. Layering onto someone else's code - reading it, understanding it, extending it - is itself a real engineering skill, and the program is structured to give you eight sprints of practice at it.

## Module 0 ramp

Module 0 is a one-week workflow dry run, not a real merge contest:

- Cut `intern/<name>/m0` from `main`.
- Open one trivial PR (e.g. add yourself to a contributors list, or write a one-paragraph "what I expect to learn" note).
- Practice the full loop: open the PR, request review, address comments, watch CI go green.
- The mentor merges everyone's PR. This is the one sprint where there's no contest.

By the time Module 1 starts, every intern has used the workflow once.

## Things to not do

- Don't merge your own PR. Only the mentor merges to `main`.
- Don't push directly to `main`. Branch protection will reject it; even if it didn't, don't.
- Don't force-push to `main` or to a branch that has an open PR with reviews on it. If you need to rewrite history on your own feature branch before review starts, fine; once reviews land, append commits.
- Don't open PRs from your sprint branch directly into `main`. Cut a feature branch per epic so each PR has a clean scope.
- Don't skip the verification section of the PR template. "It works on my machine" without a recipe is unreviewable.
- Don't review your assigned peer's PR by rubber-stamping. A useless review is worse than no review.
