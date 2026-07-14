# Bilingual README Design

## Goal

Add conventional GitHub project README files that introduce the skills in this
repository, provide English as the default language, link to a separate Chinese
translation, and make the official website and Discord community easy to find.

## Structure

The repository will use separate English and Chinese README files:

1. `README.md` is the default English document.
2. `README_zh.md` is the complete Chinese translation.
3. Both files begin with a centered hero inspired by conventional GitHub
   project pages: language links, project title, one-line description, website
   and Discord badges, and section navigation.
4. A horizontal divider separates the hero from the main content.
5. Each skill appears under a title-cased display name linked to its repository
   directory.
6. Each skill description is immediately followed by its own Hermes install
   command instead of using a separate consolidated installation section.
7. Both files end with website and community links.

## Content Boundaries

- Describe only capabilities confirmed by the existing `SKILL.md` files.
- Include the official website at `https://clawling.com`.
- Include the official Discord at `https://discord.gg/qrfNqTFaG`.
- Present the skill names as `ClawChat OfficeCLI` and `Tarot Arcana`.
- Link `ClawChat OfficeCLI` to `productivity/clawchat-officecli/`.
- Link `Tarot Arcana` to `creative/tarot-arcana/`.
- Install each skill from its raw GitHub `SKILL.md` URL using the Hermes
  documented `hermes skills install https://.../SKILL.md` form.
- Do not invent installation commands, compatibility guarantees, or roadmap
  claims that are not documented in the repository.
- Keep the document concise and suitable for the GitHub repository landing
  page.

## Verification

- Confirm the two current skills are represented accurately.
- Confirm the English and Chinese files are both present and mutually linked.
- Confirm website and Discord URLs appear correctly.
- Confirm each display name links to the matching skill directory.
- Confirm each skill has its own correct Hermes install command directly below
  its description.
- Review Markdown headings, badges, and links for valid syntax.
