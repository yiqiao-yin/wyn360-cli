# Planning & Sub-Agents

*New in v0.4.0, enhanced in v0.5.1*

WYN360 CLI introduces structured planning and parallel sub-agent workers, enabling the assistant to break complex tasks into steps and parallelize research across multiple workers.

---

## Plan Mode

Plan mode forces the AI to think through a task before executing it. Instead of jumping straight into code changes, the assistant produces a numbered plan for your approval.

### How It's Triggered

Plan mode works **two ways**:

**Automatic (AI-initiated):** The AI has `enter_plan_mode` and `exit_plan_mode` tools. When it receives a complex task (multi-file changes, architectural decisions, unclear requirements), it proactively enters plan mode, investigates the codebase, then presents a plan for approval.

**Manual (user-initiated):** Type `/plan` to check plan status, or ask the AI to plan explicitly: "Plan how to add authentication."

### The Flow

```
1. AI detects complex task → calls enter_plan_mode
2. AI investigates (reads files, searches — NO modifications)
3. AI calls exit_plan_mode with step-by-step plan
4. You see the plan → /plan approve or /plan reject
5. If approved → AI executes step by step
```

### When the AI Enters Plan Mode Automatically

The AI is instructed to use plan mode when ANY of these apply:
- **New feature** requiring architectural decisions
- **Multiple valid approaches** exist
- **3+ files** will be modified
- **Unclear requirements** need investigation first

It will NOT enter plan mode for simple tasks (typos, one-line fixes, specific instructions).

### Commands

```bash
# View current plan status
/plan

# Approve the current plan
/plan approve

# Reject and discard the current plan
/plan reject

# Skip the current step
/plan skip

# Check progress
/plan status
```

### Example Session

```
You: Refactor the auth module to use JWT tokens instead of sessions

WYN360: [Calls enter_plan_mode — investigates codebase...]
WYN360: [Reads src/auth/session.py, src/auth/middleware.py, tests/...]
WYN360: [Calls exit_plan_mode with plan:]

## Plan: Refactor auth to JWT

[ ] Step 1: Analyze current session-based auth implementation
    Files: `src/auth/session.py`, `src/auth/middleware.py`
[ ] Step 2: Create JWT token utilities
    Files: `src/auth/jwt_utils.py`
[ ] Step 3: Update authentication middleware
    Files: `src/auth/middleware.py`
[ ] Step 4: Migrate user endpoints to use JWT
    Files: `src/api/users.py`, `src/api/auth.py`
[ ] Step 5: Update tests
    Files: `tests/test_auth.py`, `tests/test_api.py`

Waiting for approval. Use /plan approve or /plan reject.

You: /plan approve
WYN360: Plan approved. Starting Step 1...

You: /plan status
2/5 steps completed

You: /plan skip
Skipped to: Step 4 - Migrate user endpoints to use JWT
```

### Plan Display Format

Each step shows:
- **Status icon**: `[ ]` pending, `[>]` in progress, `[x]` completed, `[-]` skipped
- **Description**: What the step does
- **Files**: Which files will be read or modified

### When Plans Are Created

The AI creates plans automatically for complex tasks. You can also explicitly ask:
- "Plan how to add logging to all modules"
- "Create a plan for migrating the database"
- "What steps would it take to add OAuth support?"

---

## Sub-Agent Workers

The sub-agent system allows WYN360 to spawn parallel worker agents for research, implementation, and verification tasks.

### Worker Types

| Type | Purpose | Behavior |
|------|---------|----------|
| `research` | Investigate codebase, find files | Read-only, reports findings |
| `implement` | Make targeted code changes | Writes files, commits |
| `verify` | Test and validate changes | Runs tests, checks types |
| `general` | Any task | Full capabilities |

### How It Works

When the AI needs to investigate multiple areas simultaneously, it spawns worker agents:

```
You: There's a bug in both the auth and payment modules

WYN360: Let me investigate both areas in parallel.

[Spawns worker: "Investigate auth module"]
[Spawns worker: "Investigate payment module"]

Workers: 2 total, 2 completed, 0 failed | Duration: 3200ms

### Investigate auth module
Found null pointer in src/auth/validate.py:42. The user field
is undefined when sessions expire...

### Investigate payment module
Found race condition in src/payment/charge.py:89. Two concurrent
requests can double-charge...
```

### Commands

```bash
# Show all sub-agent tasks and their status
/workers
```

The `/workers` command displays a table with:

| Column | Description |
|--------|-------------|
| ID | Unique task identifier (e.g., `agent-a1b2c3`) |
| Status | `pending`, `running`, `completed`, `failed`, `killed` |
| Type | `research`, `implement`, `verify`, `general` |
| Description | What the worker is doing |
| Duration | How long the task took |

### Concurrency

Workers respect concurrency limits (default: 3 simultaneous workers):

- **Read-only tasks** (research) run in parallel freely
- **Write tasks** (implementation) are serialized to avoid conflicts
- **Verification** can run alongside implementation on different files

### Task Lifecycle

```
pending → running → completed
                  → failed
                  → killed
```

- **Completed**: Worker finished successfully, results available
- **Failed**: Worker encountered an error (error message available)
- **Killed**: Worker was stopped (e.g., requirements changed)

### Result Synthesis

After parallel workers complete, the AI synthesizes their findings:

1. Reads all worker results
2. Identifies the approach
3. Writes specific implementation instructions
4. Directs follow-up work based on findings

This means the AI doesn't just dump raw results - it understands them and creates a coherent next step.

---

## Combining Plan Mode with Sub-Agents

For maximum effectiveness, plan mode and sub-agents work together:

1. **Planning phase**: AI creates a plan
2. **Research phase**: Sub-agents investigate in parallel
3. **Synthesis**: AI combines findings into specific implementation steps
4. **Execution phase**: Steps are executed sequentially
5. **Verification phase**: Sub-agent verifies changes

This mirrors professional software engineering workflows where you research, plan, implement, then verify.

---

**Next:** [Hooks & Token Budget](hooks-and-budget.md) | [Commands Reference](../usage/commands.md)
