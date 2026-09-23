# Skill candidate: <proposed-name>

<!--
A skill is an on-demand workflow the agent discovers by its description. Each
active skill costs discovery attention in every session, so promote only a
judgment-heavy workflow that has repeated. A one-off lesson belongs in a
knowledge note; a mandatory behavior belongs in a rule. Review with
playbooks/skill-portfolio-review.md.
-->

## Identity and lifecycle

- Proposed name: `<verb-noun>`
- Scope: `<project | personal | shared plugin>`
- Status: `<candidate | trial | active | deprecated | retired>`
- Owner: `<role>`
- Next review: `<YYYY-MM-DD>`

## Evidence for promotion

- Observed repetitions (at least two) or high-consequence reason: <evidence>
- Overlap checked against rules, playbooks, knowledge, tools, other skills: <result>
- Why a rule or script is not enough: <reason>

## Baseline and delta

- Baseline behavior without the skill: <observed>
- Expected change with the skill: <observed or measured>
- Regression or negative evidence: <what got worse, or none seen>

## Discovery contract

- Use when: <trigger>
- Do not use when: <nearby job it must not claim>
- Invocation: `<implicit | explicit only>`
- Positive routing prompts: <2-3 examples that must trigger it>
- Negative routing prompts: <2-3 nearby examples that must not>

## Execution contract

- Inputs: <required>
- Outputs: <produced>
- Verification: <evidence the run succeeded>
- Failure handling and rollback: <what it does on failure>
- Dependencies: <tools, permissions>

## Retirement

- Retire when: <observable trigger, e.g. host ships the capability natively>

## Boundary confirmation

- [ ] No source-bound, employer-owned, secret, or identifying material.
- [ ] Human ownership and disclosure review completed.
- [ ] Scheduled automation will not install, enable, disable, or delete it.
