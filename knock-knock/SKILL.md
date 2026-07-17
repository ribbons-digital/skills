---
name: knock-knock
description: Use this skill for planning, discovering, or debriefing non-trivial work. Invoke it when the user wants to write an implementation plan or structure a feature before building; do a blindspot or discovery pass before starting ("knock-knock", "what am I missing?", unfamiliar codebase or domain); prepare a handoff prompt for a long agent run; clarify fuzzy requirements through brainstorming or interviews ("I'll know it when I see it"); verify understanding of a completed change ("did I miss anything?", "quiz me on this diff", "I want to make sure I understand this"); or package finished work into a pitch for buy-in. Skip for mechanical tasks - typos, renames, formatting - and simple factual questions.
disable-model-invocation: true
---

# Knock-Knock: Finding Your Unknowns

The prompt is a map. The codebase, the domain, and the real world are the territory. The gap between them is made of **unknowns** - and when the agent hits one, it guesses. The bigger the task, the more guesses. This skill is a repeatable process for shrinking that gap: surface the user's unknowns *before* they become expensive, keep tracking them *during* the work, and verify understanding *after*.

Who's there? The things you didn't know you didn't know.

## Step 0: Classify the unknowns

Before picking a technique, sort the task's information into four quadrants:

| Quadrant | Definition | Signal |
|---|---|---|
| **Known knowns** | What's already in the prompt | Explicit requirements |
| **Known unknowns** | Gaps the user knows exist but hasn't resolved | "I haven't decided how X should work" |
| **Unknown knowns** | Taste/standards the user holds but never states | "I'll know it when I see it" |
| **Unknown unknowns** | Factors the user hasn't considered at all | New domain, new codebase area, "what am I missing?" |

Quality bottlenecks live in the bottom two quadrants. The goal of every technique below is to migrate items upward into explicit instructions or named open questions.

Calibration matters in both directions: over-specified instructions get followed off a cliff when a pivot was warranted; under-specified ones get filled with generic best practices that may not fit. Surfacing unknowns is what tells you which failure mode you're near.

Establish the user's starting point before choosing a technique, because unknowns are relative to the person.
If the prompt already states their experience with the domain or codebase, treat that as the starting point and proceed instead of asking them to repeat it.
Only when the starting point is absent, ask one calibration question and wait.

## Choosing a technique

Don't run every technique every time. Match the dominant quadrant and the phase of work:

- Mostly **unknown unknowns** (new domain/area) → Blindspot pass, then teach-me loop
- Mostly **unknown knowns** (taste-driven, "I'll know it when I see it") → Brainstorms & prototypes
- Mostly **known unknowns** (identified gaps) → Interview
- User can't articulate what they want but can point at an example → References
- Ready to build → Implementation plan (decisions-first)
- Building → Implementation notes
- Built → Quiz, then pitch/explainer for stakeholders

For trivial tasks, skip straight to doing the work. This process is for tasks large enough that a wrong guess compounds.

## Pre-implementation techniques

### 1. Blindspot pass

When the user is entering unfamiliar territory, proactively scan the codebase/domain and report what they likely don't know to ask about: relevant history, conventions, potholes, what "good" looks like, and what questions an expert would ask that they haven't. Frame the output as "here's what you didn't know to ask, and here's how to prompt me better because of it."
Complete the grounded scan and blindspot report in that response when the user's starting point is already known.
Do not replace the requested pass with an interview, brainstorm, or implementation plan; any closing questions belong in the derived "how to prompt better" guidance.

Example user prompt this serves:
> "I'm adding a new auth provider but know nothing about the auth modules here. Do a blindspot pass - find my unknown unknowns and help me prompt you better."

If the user doesn't know what good looks like in a domain (e.g., color grading, database indexing, typography), don't just generate options - **teach the domain first**. Options are useless to someone who can't evaluate them. Explain the axes of quality, then generate variants for them to react to.

### 2. Brainstorms & prototypes

For taste-driven work, generate multiple genuinely different directions cheaply and let the user react. Reacting reveals unknown knowns far faster than describing does. Prefer disposable artifacts (a single mock HTML page with fake data, a throwaway script, a sketch) over wiring anything real - small spec changes cause drastically different implementations, so find them before code exists.

Start non-trivial sessions with a short exploration/brainstorm phase to set scope: surface high-value approaches the user missed, and check whether the stated problem is even the right one to solve.

Example prompts this serves:
> "Make one HTML page with 4 wildly different design directions so I can react."
> "Users churn after onboarding - search the codebase and brainstorm 10 interventions, cheapest to most ambitious."

### 3. Interview

When gaps are identified but unresolved, interview the user **one question at a time**, prioritizing questions whose answers would change the architecture or approach. Stop when remaining ambiguities wouldn't change the plan.

### 4. References

When the user can't describe what they want, ask for a reference - and prefer **source code over screenshots or descriptions**, even across languages. Read the reference's actual implementation and extract the semantics, structure, and decisions worth porting.

Example prompt this serves:
> "The Rust crate in vendor/rate-limiter has the exact backoff behavior I want. Read it and reimplement the same semantics in our TypeScript client."

### 5. Implementation plan (decisions-first)

Before building, produce a plan ordered by *likelihood the user will want to change it*: data model changes, type interfaces, and user-facing behavior at the top; mechanical refactoring buried at the bottom with a note that it needs no review. The plan's job is to surface the decisions that are actually the user's to make.

Once approved, recommend starting a fresh session/context with the plan and any prototypes passed in as artifacts.

## During implementation

### 6. Implementation notes

No amount of planning eliminates unknown unknowns - edge cases in the territory will force deviations. Keep a running `implementation-notes.md` logging every assumption made and every deviation from the plan, with a `Deviations` section. When forced off-plan, pick the conservative option, log it, and keep going rather than stopping. These notes are the raw material for the user's post-hoc review and for improving the next attempt's prompt.

## Post-implementation

### 7. Quiz

After a long session, the user's mental model lags the actual change - diffs alone don't convey behavior that depends on existing code paths. Produce a report (context, intuition, what was done and why) ending in a quiz of 3-7 questions, prioritizing behavior that depends on existing code paths over surface diff content. The user's bar: **don't merge until you pass the quiz cleanly.** Wrong answers reveal exactly where their map still diverges from the territory.

### 8. Pitch / explainer

Shipping needs buy-in. Package the spec, prototype, and implementation notes into a single artifact for reviewers - leading with a demo - so reviewers who start with the same unknowns the user had get them resolved up front, and experts can see the known failure points were accounted for.

## Closing loop

When a long-horizon task comes back wrong, diagnose it as one of two failures: not enough time spent surfacing unknowns, or a plan too rigid for the agent to improvise through the unknowns that remained. Feed the implementation notes and quiz misses back into the next attempt's prompt.

Every explainer, brainstorm, interview, prototype, and reference is a cheap way to find out what the user didn't know - before it gets expensive to fix.
