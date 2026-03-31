"""Unit tests for the hook system."""

import pytest
from wyn360_cli.hooks import (
    HookManager, HookPoint, HookContext, HookResult, RegisteredHook,
)


class TestHookResult:
    def test_defaults(self):
        r = HookResult()
        assert not r.stop_chain
        assert r.modified_message is None
        assert r.modified_response is None
        assert r.extra_messages == []
        assert not r.block_action


class TestHookManager:
    def setup_method(self):
        self.mgr = HookManager()

    def test_register_hook(self):
        def my_hook(ctx):
            return HookResult()

        hook = self.mgr.register("test_hook", HookPoint.PRE_QUERY, my_hook)
        assert hook.name == "test_hook"
        assert hook.enabled
        hooks = self.mgr.list_hooks(HookPoint.PRE_QUERY)
        assert len(hooks) == 1

    def test_unregister_hook(self):
        self.mgr.register("test", HookPoint.PRE_QUERY, lambda ctx: HookResult())
        self.mgr.unregister("test")
        assert len(self.mgr.list_hooks(HookPoint.PRE_QUERY)) == 0

    def test_unregister_specific_point(self):
        fn = lambda ctx: HookResult()
        self.mgr.register("test", HookPoint.PRE_QUERY, fn)
        self.mgr.register("test", HookPoint.POST_RESPONSE, fn)
        self.mgr.unregister("test", HookPoint.PRE_QUERY)
        assert len(self.mgr.list_hooks(HookPoint.PRE_QUERY)) == 0
        assert len(self.mgr.list_hooks(HookPoint.POST_RESPONSE)) == 1

    def test_enable_disable(self):
        self.mgr.register("test", HookPoint.PRE_QUERY, lambda ctx: HookResult())
        self.mgr.enable("test", False)
        hooks = self.mgr.list_hooks(HookPoint.PRE_QUERY)
        assert not hooks[0].enabled
        self.mgr.enable("test", True)
        assert self.mgr.list_hooks(HookPoint.PRE_QUERY)[0].enabled

    @pytest.mark.asyncio
    async def test_execute_sync_hook(self):
        def my_hook(ctx):
            return HookResult(modified_message="modified!")

        self.mgr.register("mod", HookPoint.PRE_QUERY, my_hook)
        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="original")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert result.modified_message == "modified!"

    @pytest.mark.asyncio
    async def test_execute_async_hook(self):
        async def my_hook(ctx):
            return HookResult(modified_response="async result")

        self.mgr.register("async_mod", HookPoint.POST_RESPONSE, my_hook)
        ctx = HookContext(hook_point=HookPoint.POST_RESPONSE, response="original")
        result = await self.mgr.execute(HookPoint.POST_RESPONSE, ctx)
        assert result.modified_response == "async result"

    @pytest.mark.asyncio
    async def test_hook_chain(self):
        def hook1(ctx):
            return HookResult(modified_message=ctx.message + " +hook1")

        def hook2(ctx):
            return HookResult(modified_message=ctx.message + " +hook2")

        self.mgr.register("h1", HookPoint.PRE_QUERY, hook1, priority=0)
        self.mgr.register("h2", HookPoint.PRE_QUERY, hook2, priority=1)

        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="start")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert result.modified_message == "start +hook1 +hook2"

    @pytest.mark.asyncio
    async def test_stop_chain(self):
        def hook1(ctx):
            return HookResult(modified_message="first", stop_chain=True)

        def hook2(ctx):
            return HookResult(modified_message="second")

        self.mgr.register("h1", HookPoint.PRE_QUERY, hook1, priority=0)
        self.mgr.register("h2", HookPoint.PRE_QUERY, hook2, priority=1)

        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="start")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert result.modified_message == "first"

    @pytest.mark.asyncio
    async def test_disabled_hooks_skipped(self):
        def my_hook(ctx):
            return HookResult(modified_message="should not appear")

        self.mgr.register("disabled", HookPoint.PRE_QUERY, my_hook)
        self.mgr.enable("disabled", False)

        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="original")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert result.modified_message is None

    @pytest.mark.asyncio
    async def test_hook_exception_handled(self):
        def bad_hook(ctx):
            raise RuntimeError("hook exploded")

        self.mgr.register("bad", HookPoint.PRE_QUERY, bad_hook)
        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="test")
        # Should not raise
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert result.modified_message is None

    @pytest.mark.asyncio
    async def test_extra_messages(self):
        def warn_hook(ctx):
            return HookResult(extra_messages=["Warning: something dangerous"])

        self.mgr.register("warn", HookPoint.PRE_QUERY, warn_hook)
        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="rm -rf /")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert len(result.extra_messages) == 1

    @pytest.mark.asyncio
    async def test_block_action(self):
        def blocker(ctx):
            return HookResult(block_action=True, block_reason="dangerous")

        self.mgr.register("block", HookPoint.PRE_TOOL, blocker)
        ctx = HookContext(hook_point=HookPoint.PRE_TOOL, tool_name="execute_command")
        result = await self.mgr.execute(HookPoint.PRE_TOOL, ctx)
        assert result.block_action
        assert result.block_reason == "dangerous"

    def test_get_stats(self):
        self.mgr.register("a", HookPoint.PRE_QUERY, lambda ctx: HookResult())
        self.mgr.register("b", HookPoint.POST_RESPONSE, lambda ctx: HookResult())
        stats = self.mgr.get_stats()
        assert stats["total_registered"] == 2

    def test_register_builtin_hooks(self):
        self.mgr.register_builtin_hooks()
        hooks = self.mgr.list_hooks()
        names = [h.name for h in hooks]
        assert "builtin_safety_check" in names
        assert "builtin_response_tracker" in names

    @pytest.mark.asyncio
    async def test_builtin_safety_hook(self):
        self.mgr.register_builtin_hooks()
        ctx = HookContext(hook_point=HookPoint.PRE_QUERY, message="please rm -rf everything")
        result = await self.mgr.execute(HookPoint.PRE_QUERY, ctx)
        assert len(result.extra_messages) > 0
        assert "destructive" in result.extra_messages[0].lower()

    def test_priority_ordering(self):
        self.mgr.register("low", HookPoint.PRE_QUERY, lambda ctx: HookResult(), priority=10)
        self.mgr.register("high", HookPoint.PRE_QUERY, lambda ctx: HookResult(), priority=-10)
        self.mgr.register("mid", HookPoint.PRE_QUERY, lambda ctx: HookResult(), priority=0)
        hooks = self.mgr.list_hooks(HookPoint.PRE_QUERY)
        assert hooks[0].name == "high"
        assert hooks[1].name == "mid"
        assert hooks[2].name == "low"
