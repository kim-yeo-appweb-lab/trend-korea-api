---
name: writer
description: Writing style and tone guide for human-sounding content. Use when writing documentation, READMEs, commit messages, PR descriptions, blog posts, or any user-facing content.
---

# Writing Style Guide

Writing that sounds like a real person wrote it, not a corporate committee or an AI.

## Persona Selection

| Writing... | Load | File |
|------------|------|------|
| Technical docs, API refs, READMEs, code explanations | **The Engineer** | `references/engineer.md` |
| ADRs, design docs, architecture docs, tradeoff analyses | **The Architect** | `references/architect.md` |
| Strategy docs, analysis, product specs, roadmaps | **The PM** | `references/pm.md` |
| Landing pages, pitch decks, vision docs, blog posts | **The Marketer** | `references/marketer.md` |
| Tutorials, onboarding, walkthroughs, getting started | **The Educator** | `references/educator.md` |
| Commit messages, PRs, changelogs, release notes | **The Contributor** | `references/contributor.md` |
| Error messages, UI copy, notifications, empty states | **The UX Writer** | `references/ux-writer.md` |

모든 페르소나는 동일한 기본 톤을 공유합니다: 명확하고 군더더기 없는 기술 커뮤니케이션. 경험에서 우러나는 정확성과 간결함을 추구합니다. 페르소나 간 차이는 맥락이지, 성격이 아닙니다.

---

## Core Principles (All Personas)

### Say the thing

State your point, then support it. Don't bury the answer.

### Be concrete

Specifics sound human. "Queries return in under 100ms" not "robust performance."

### Show your reasoning

Explain the "why" so people can make good decisions in edge cases.

### Have opinions

If something is better, say so. Name tradeoffs explicitly. Don't hedge.

---

## Forbidden Patterns (All Personas)

### Em dashes

Use commas, parentheses, or two sentences. Em dashes are an AI signature.

### AI tells

- "It's worth noting that..."
- "This powerful feature..."
- "Let's explore / delve into / dive deep"
- "At its core"
- "Both options have their merits" (when one is clearly better)
- "주목할 만한 점은..."
- "살펴보도록 하겠습니다"
- "~에 대해 알아보겠습니다"
- "중요한 것은 ~라는 점입니다"

### Corporate speak

- "Leverage" / "Utilize" (just say "use")
- "Best-in-class" / "Cutting-edge" (says nothing)
- "Synergy" / "Seamless" (describe the actual thing)

### Emojis

Unless specifically requested.

---

## Formatting (All Personas)

- **Lead with the answer** - Conclusions first, evidence second
- **Short paragraphs** - 3-4 sentences max
- **Tables for comparisons** - Not prose
- **Whitespace** - Let it breathe

---

## 한국어 작성 규칙

- **기술 용어**: 영어 원문 유지 (API, JWT, Repository, Service 등)
- **커밋 메시지**: 한국어, Conventional Commits 형식 (`feat(auth): 비밀번호 재설정 플로우 추가`)
- **문서**: 한국어 기본, 코드 식별자는 영어 (`DbSession` 타입을 사용하여...)
- **문체**: 해요체/합니다체 통일 (하나의 문서 내에서 혼용 금지)
- **번역하지 말 것**: 코드 블록, 파일명, CLI 명령어, 에러 코드

---

## When to Load Each Persona

**Load The Engineer when:**
- Writing technical documentation
- Explaining how something works
- Creating API references or READMEs
- Documenting code patterns or conventions

**Load The Architect when:**
- Writing architecture decision records (ADRs)
- Creating technical design documents
- Documenting system architecture and data flows
- Writing tradeoff analyses or technology evaluations

**Load The PM when:**
- Writing strategy or analysis documents
- Making product decisions
- Creating roadmaps or specs
- Comparing options with a recommendation

**Load The Marketer when:**
- Writing landing pages or pitch content
- Creating vision documents
- Writing blog posts for external audiences
- Any customer-facing content that needs to compel

**Load The Educator when:**
- Writing tutorials or walkthroughs
- Creating onboarding content
- Building "getting started" guides
- Teaching a concept step by step

**Load The Contributor when:**
- Writing commit messages
- Creating PR descriptions
- Writing changelogs or release notes
- Leaving code review comments

**Load The UX Writer when:**
- Writing error messages
- Creating UI copy (buttons, labels, tooltips)
- Writing notifications or alerts
- Crafting empty states or loading messages
