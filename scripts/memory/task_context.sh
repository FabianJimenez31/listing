#!/bin/bash
# Branch-derived task identity and the memory quota it must satisfy.
#
# The quota scales with the branch prefix on purpose. Demanding all seven memory
# classes from a one-line chore produces ritual filling, and memory filled as a
# ritual is worse than no memory: it pollutes future searches with noise that
# looks like signal.

# The seven classes. Five are written per task, one is derived from the session
# timeline, and one is personal scope shared across projects.
MEM_CLASS_ALL="contextual episodic semantic procedural decision preferences outcome"

# Slug derivation is delegated to common.sh so this file, pre-commit.sh and
# check-prerequisites.sh cannot disagree about what a valid task id is.
# Sourced once here rather than per call: mem_task_slug runs on every hook.
_MEM_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ -f "$_MEM_REPO_ROOT/.specify/scripts/bash/common.sh" ]; then
    # shellcheck source=/dev/null
    source "$_MEM_REPO_ROOT/.specify/scripts/bash/common.sh"
fi

mem_task_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# feature | fix | hotfix | chore | other
mem_task_kind() {
    local branch
    branch="$(mem_task_branch)"
    case "$branch" in
        feature/*) echo "feature" ;;
        fix/*)     echo "fix" ;;
        hotfix/*)  echo "hotfix" ;;
        chore/*)   echo "chore" ;;
        *)         echo "other" ;;
    esac
}

mem_task_slug() {
    local branch
    branch="$(mem_task_branch)"
    if command -v spec_kit_effective_branch_name >/dev/null 2>&1; then
        spec_kit_effective_branch_name "$branch"
    else
        printf '%s\n' "${branch##*/}"
    fi
}

# Classes required before a branch of this kind may be pushed.
mem_task_required_classes() {
    case "$(mem_task_kind)" in
        feature)     echo "$MEM_CLASS_ALL" ;;
        fix|hotfix)  echo "decision outcome semantic" ;;
        chore)       echo "decision" ;;
        *)           echo "" ;;
    esac
}

# Engram observation type for each class.
mem_class_type() {
    case "$1" in
        semantic)    if [ "$(mem_task_kind)" = "fix" ] || [ "$(mem_task_kind)" = "hotfix" ]; then
                         echo "bugfix"
                     else
                         echo "architecture"
                     fi ;;
        procedural)  echo "pattern" ;;
        decision)    echo "decision" ;;
        outcome)     echo "learning" ;;
        preferences) echo "config" ;;
        *)           echo "discovery" ;;
    esac
}

# Canonical topic_key for a class on the current task.
mem_class_topic_key() {
    local class="$1"
    case "$class" in
        preferences) echo "user/preferences" ;;
        contextual|episodic) echo "" ;;
        *) printf 'spec/%s/%s\n' "$(mem_task_slug)" "$class" ;;
    esac
}

mem_class_scope() {
    case "$1" in
        preferences) echo "personal" ;;
        *)           echo "project" ;;
    esac
}

mem_class_label() {
    case "$1" in
        contextual)  echo "contextual (session)" ;;
        episodic)    echo "episodic (timeline)" ;;
        semantic)    echo "semantic (architecture)" ;;
        procedural)  echo "procedural (how)" ;;
        decision)    echo "decision (what and why)" ;;
        preferences) echo "preferences (user constraints)" ;;
        outcome)     echo "outcome (what happened next)" ;;
        *)           echo "$1" ;;
    esac
}
