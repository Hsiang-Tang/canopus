# Assumptions-first

Rule: [`rules/development.md`](../../rules/development.md) (Minimum delivery
contract step 2; Assumptions-first). There is deliberately no tool, field, or
template: the step costs one short message and should stay that cheap.

## The problem

Faced with an ambiguous request, an agent has two bad defaults:

- **Guess and build.** It fills gaps with plausible assumptions and delivers
  something polished. The owner discovers the wrong assumption at review, after
  the cost is spent.
- **Interrogate.** It asks a long list of open-ended questions. The owner has
  to do the design work to answer them, and often cannot say which questions
  matter.

Neither exposes the one thing the owner needs to see: which guesses are
expensive if wrong.

## The idea

Before material work on an ambiguous request, state three to five
assumptions, each with the cost of being wrong. The owner reads a short list,
corrects the one or two that matter, and says go. The confirmed assumptions
go into the spec or the task Issue, so later sessions inherit them.

- **Three to five** keeps the list readable and forces prioritization. If
  there are more, the request needs a spec conversation, not a list.
- **Cost of being wrong** is the useful part. It lets the owner skim cheap
  assumptions and focus on expensive ones.
- **Assumptions, not questions.** "I assume X" can be confirmed in one word.
  "What should X be?" asks the owner to design.

Skip the step when the request is clear. The goal is not ceremony; it is
catching the expensive misunderstanding before it is built.

## Example

Request on a synthetic `docs-site`: "Add a changelog page."

```text
Before I start, my assumptions:

1. The page is generated from existing changelog.d/ fragments, not written by
   hand. If wrong: I build a generator nobody wants; about half the work.
2. Newest release first, one section per release. If wrong: a template
   change; cheap.
3. Unreleased fragments are hidden. If wrong: readers see unfinished changes;
   cheap to flip, awkward if published.
4. No RSS feed in this task. If wrong: a follow-up task; cheap.
5. The URL is /changelog/. If wrong: a broken link if someone already linked a
   different path; cheap now, expensive after launch.

Confirm or correct, and I will freeze these into the acceptance list.
```

The owner replies "1 is wrong: we write it by hand. Rest fine." That one line
saved building a generator. Assumptions 2–5 become acceptance items
(`AC1-order`, `AC2-hide-unreleased`, `AC3-url`) and assumption 4 goes into the
envelope as out of scope.

## How it connects

Confirmed assumptions are the raw material for the frozen envelope
([north-star-and-envelope.md](north-star-and-envelope.md)). An unconfirmed
assumption that later turns out wrong is a scope change, which the convergence
evaluator treats as `REALIGN` until the owner re-admits.
