"""Protect consumer edits before Spec Kit unregisters the retired .NET skill."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch


SKILL = "speckit-program-kit-dotnet-sync"
COMMAND = "speckit.program-kit-dotnet.sync"


def command_outputs(repository: Path) -> list[Path]:
    from specify_cli.agents import CommandRegistrar
    registrar = CommandRegistrar()
    results = set()
    directories = {registrar._resolve_agent_dir(agent, config, repository) for agent, config in registrar.AGENT_CONFIGS.items()}
    directories.update(repository / relative for relative in ('.github/prompts', '.codex/prompts'))
    for directory in directories:
        if not directory.resolve().is_relative_to(repository.resolve()) or not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.is_file() and any(path.name in {name + suffix for suffix in ('.md','.toml','.yaml','.agent.md','.prompt.md')} for name in (COMMAND, SKILL)):
                results.add(path)
    return sorted(results)


def preflight(repository: Path) -> None:
    from specify_cli import load_init_options
    from specify_cli.agents import CommandRegistrar
    from specify_cli.extensions import ExtensionManager, ExtensionManifest

    installed = repository / ".specify/extensions/program-kit-dotnet"
    manifest_path = installed / "extension.yml"
    if not manifest_path.is_file():
        return
    manifest = ExtensionManifest(manifest_path)
    if not any(command["name"] == COMMAND for command in manifest.commands):
        return
    manager = ExtensionManager(repository)
    outputs = []
    for directory in manager._extension_skill_candidate_dirs():
        skill = directory / SKILL / "SKILL.md"
        if not skill.exists():
            continue
        if not skill.resolve().is_relative_to(repository.resolve()):
            raise ValueError(f"PKU117 retired skill escapes this consumer: {skill}")
        extra = [path for path in skill.parent.rglob("*") if path.is_file() and path != skill]
        if extra:
            raise ValueError(f"PKU117 retired skill contains consumer files; relocate them before upgrade: {extra}")
        outputs.append(skill)
    raw_outputs = command_outputs(repository)
    if not outputs and not raw_outputs:
        return
    # Render with the installed Spec Kit registrar and original command, preserving the real
    # project root for placeholder resolution. Only the output directory is redirected to temp.
    # No install/uninstall action or global integration output is used to establish ownership.
    expected = set()
    options = load_init_options(repository) or {}
    registrar = CommandRegistrar()
    expected_commands = set()
    command = next(command for command in manifest.commands if command['name'] == COMMAND)
    frontmatter, body = registrar.parse_frontmatter((installed / command['file']).read_text(encoding='utf-8'))
    frontmatter = registrar._adjust_script_paths(frontmatter, extension_id=manifest.id)
    body = registrar.rewrite_extension_paths(body, manifest.id, installed)
    for agent in registrar.AGENT_CONFIGS:
        expected.add(registrar.render_skill_command(agent, SKILL, frontmatter, body, manifest.id,
                                                    command['file'], repository, extension_id=manifest.id))
        with tempfile.TemporaryDirectory(prefix="program-kit-retired-skill-") as directory:
            output = Path(directory)
            with patch.object(manager, "_get_skills_dir", return_value=output), patch("specify_cli.load_init_options", return_value={**options, "ai": agent}):
                manager._register_extension_skills(manifest, installed)
            rendered = output / SKILL / "SKILL.md"
            if rendered.is_file():
                expected.add(rendered.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix='program-kit-retired-command-') as directory:
            output = Path(directory)
            with patch.object(registrar, '_resolve_agent_dir', return_value=output), patch.object(registrar, 'write_copilot_prompt'):
                registrar.register_commands(agent, [command], manifest.id, installed, repository,
                    context_note=f'\n<!-- Extension: {manifest.id} -->\n<!-- Config: .specify/extensions/{manifest.id}/ -->\n',
                    extension_id=manifest.id)
            if agent == 'copilot':
                registrar.write_copilot_prompt(output, COMMAND)
            expected_commands.update(path.read_text(encoding='utf-8') for path in output.rglob('*') if path.is_file())
    for skill in outputs:
        if skill.read_text(encoding="utf-8") not in expected:
            raise ValueError(f"PKU117 retired skill has consumer edits; relocate those edits before upgrade: {skill}")
    for path in raw_outputs:
        if path.read_text(encoding='utf-8') not in expected_commands:
            raise ValueError(f'PKU117 retired command has consumer edits; relocate those edits before upgrade: {path}')


def verify_removed(repository: Path) -> None:
    from specify_cli.extensions import ExtensionManager
    manager = ExtensionManager(repository)
    remaining = [str(directory / SKILL) for directory in manager._extension_skill_candidate_dirs()
                 if (directory / SKILL).exists()]
    remaining.extend(str(path) for path in command_outputs(repository))
    if remaining:
        raise ValueError(f"PKU117 retired sync integration remains registered: {remaining}")
