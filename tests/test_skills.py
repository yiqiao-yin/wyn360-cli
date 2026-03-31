"""Unit tests for the skills system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from wyn360_cli.skills import Skill, SkillRegistry


class TestSkill:
    def test_render_prompt_basic(self):
        skill = Skill(name="test", description="Test skill", prompt="Hello {args}")
        assert skill.render_prompt("world") == "Hello world"

    def test_render_prompt_no_args(self):
        skill = Skill(name="test", description="Test", prompt="No args here")
        assert skill.render_prompt() == "No args here"

    def test_render_prompt_cwd(self):
        skill = Skill(name="test", description="Test", prompt="Dir: {cwd}")
        rendered = skill.render_prompt()
        assert str(Path.cwd()) in rendered

    def test_render_prompt_double_braces(self):
        skill = Skill(name="test", description="Test", prompt="Args: {{args}}")
        # {{args}} -> {foo} because inner {args} is replaced first, leaving outer braces
        assert skill.render_prompt("foo") == "Args: {foo}"


class TestSkillRegistry:
    def setup_method(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.user_dir = self.test_dir / "user_skills"
        self.project_dir = self.test_dir / "project_skills"
        self.user_dir.mkdir()
        self.project_dir.mkdir()
        self.registry = SkillRegistry(
            user_skills_dir=self.user_dir,
            project_skills_dir=self.project_dir,
        )

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def test_load_empty(self):
        self.registry.load_all()
        assert self.registry.list_skills() == []

    def test_load_yaml_skill(self):
        skill_file = self.user_dir / "review.yaml"
        skill_file.write_text("""
name: review
description: Code review helper
prompt: Review the code in {cwd}. {args}
aliases:
  - cr
""")
        self.registry.load_all()
        assert self.registry.has_skill("review")
        assert self.registry.has_skill("cr")

        skill = self.registry.get_skill("review")
        assert skill.description == "Code review helper"

    def test_alias_lookup(self):
        skill_file = self.user_dir / "test.yaml"
        skill_file.write_text("""
name: test-skill
description: A test
prompt: Do the test
aliases:
  - ts
  - test
""")
        self.registry.load_all()
        assert self.registry.get_skill("ts") is not None
        assert self.registry.get_skill("test") is not None
        assert self.registry.get_skill("ts").name == "test-skill"

    def test_project_overrides_user(self):
        # User skill
        (self.user_dir / "deploy.yaml").write_text("""
name: deploy
description: User deploy
prompt: Deploy using user method
""")
        # Project skill with same name
        (self.project_dir / "deploy.yaml").write_text("""
name: deploy
description: Project deploy
prompt: Deploy using project method
""")
        self.registry.load_all()
        skill = self.registry.get_skill("deploy")
        assert skill.description == "Project deploy"

    def test_register_builtin(self):
        builtin = Skill(
            name="commit",
            description="Git commit helper",
            prompt="Create a commit for {args}",
        )
        self.registry.register_builtin(builtin)
        assert self.registry.has_skill("commit")
        assert self.registry.get_skill("commit").source == "builtin"

    def test_get_nonexistent(self):
        self.registry.load_all()
        assert self.registry.get_skill("nope") is None
        assert not self.registry.has_skill("nope")

    def test_yml_extension(self):
        skill_file = self.user_dir / "lint.yml"
        skill_file.write_text("""
name: lint
description: Run linter
prompt: Run linting on {cwd}
""")
        self.registry.load_all()
        assert self.registry.has_skill("lint")

    def test_skip_skill_without_prompt(self):
        skill_file = self.user_dir / "bad.yaml"
        skill_file.write_text("""
name: bad
description: No prompt skill
""")
        self.registry.load_all()
        assert not self.registry.has_skill("bad")

    def test_create_example_skill(self):
        example_dir = self.test_dir / "examples"
        SkillRegistry.create_example_skill(example_dir)
        assert (example_dir / "example_review.yaml").exists()

    def test_list_skills(self):
        (self.user_dir / "a.yaml").write_text("name: alpha\ndescription: A\nprompt: do A")
        (self.user_dir / "b.yaml").write_text("name: beta\ndescription: B\nprompt: do B")
        self.registry.load_all()
        skills = self.registry.list_skills()
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert "alpha" in names
        assert "beta" in names
