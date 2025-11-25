"""Unit tests for browse_and_find agent tool integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.agent import WYN360Agent


class TestBrowseAndFindTool:
    """Test browse_and_find tool integration with WYN360Agent."""

    @pytest.mark.asyncio
    async def test_browse_and_find_success(self):
        """Test successful browse_and_find execution."""
        agent = WYN360Agent(api_key="test_key")

        # Mock BrowserTaskExecutor
        with patch('wyn360_cli.agent.BrowserTaskExecutor') as MockExecutor:
            mock_executor_instance = AsyncMock()
            MockExecutor.return_value = mock_executor_instance

            # Mock successful execution result
            mock_executor_instance.execute_task = AsyncMock(return_value={
                'status': 'success',
                'result': {'price': '$99.99', 'product': 'Sneakers'},
                'steps_taken': 5,
                'reasoning': 'Found the cheapest sneaker successfully',
                'history': []
            })

            # Execute browse_and_find
            result = await agent.browse_and_find(
                ctx=None,
                task="Find the cheapest sneaker",
                url="https://amazon.com",
                max_steps=20,
                headless=False
            )

            # Verify
            assert '✅' in result
            assert 'Task Completed Successfully' in result
            assert 'price' in result or '$99.99' in result
            assert '5' in result  # steps taken

            # Verify executor was called correctly
            MockExecutor.assert_called_once_with(agent.agent)
            mock_executor_instance.execute_task.assert_called_once_with(
                task="Find the cheapest sneaker",
                url="https://amazon.com",
                max_steps=20,
                headless=False
            )

    @pytest.mark.asyncio
    async def test_browse_and_find_partial(self):
        """Test browse_and_find with partial completion."""
        agent = WYN360Agent(api_key="test_key")

        with patch('wyn360_cli.agent.BrowserTaskExecutor') as MockExecutor:
            mock_executor_instance = AsyncMock()
            MockExecutor.return_value = mock_executor_instance

            # Mock partial completion result
            mock_executor_instance.execute_task = AsyncMock(return_value={
                'status': 'partial',
                'result': None,
                'steps_taken': 20,
                'reasoning': 'Reached maximum steps without completion',
                'history': [
                    {'step': 1, 'action': {'type': 'click'}, 'confidence': 80, 'reasoning': 'Clicked button'},
                    {'step': 2, 'action': {'type': 'type'}, 'confidence': 75, 'reasoning': 'Typed query'}
                ]
            })

            result = await agent.browse_and_find(
                ctx=None,
                task="Complex task",
                url="https://example.com"
            )

            # Verify
            assert '⚠️' in result
            assert 'Partially Completed' in result
            assert '20' in result
            assert 'Increase max_steps' in result

    @pytest.mark.asyncio
    async def test_browse_and_find_failed(self):
        """Test browse_and_find with failed execution."""
        agent = WYN360Agent(api_key="test_key")

        with patch('wyn360_cli.agent.BrowserTaskExecutor') as MockExecutor:
            mock_executor_instance = AsyncMock()
            MockExecutor.return_value = mock_executor_instance

            # Mock failed result
            mock_executor_instance.execute_task = AsyncMock(return_value={
                'status': 'failed',
                'result': None,
                'steps_taken': 3,
                'reasoning': 'Agent appears stuck. Unable to make progress.',
                'history': [
                    {'step': 1, 'action': {'type': 'click', 'selector': '#btn'}, 'confidence': 50, 'reasoning': 'Tried clicking'},
                    {'step': 2, 'action': {'type': 'click', 'selector': '#btn'}, 'confidence': 50, 'reasoning': 'Tried again'},
                    {'step': 3, 'action': {'type': 'click', 'selector': '#btn'}, 'confidence': 50, 'reasoning': 'Tried once more'}
                ]
            })

            result = await agent.browse_and_find(
                ctx=None,
                task="Impossible task",
                url="https://example.com"
            )

            # Verify
            assert '❌' in result
            assert 'Task Failed' in result
            assert 'stuck' in result.lower()
            assert 'Suggestions' in result

    @pytest.mark.asyncio
    async def test_browse_and_find_bedrock_mode(self):
        """Test that browse_and_find is disabled in Bedrock mode."""
        # Mock Bedrock mode
        with patch('wyn360_cli.agent._validate_aws_credentials', return_value=(True, "")):
            # Create agent in Bedrock mode
            agent = WYN360Agent(use_bedrock=True)

            result = await agent.browse_and_find(
                ctx=None,
                task="Test task",
                url="https://example.com"
            )

            # Verify error message
            assert '❌' in result
            assert 'vision capabilities' in result.lower()
            assert 'Bedrock mode' in result or 'bedrock' in result.lower()
            assert 'ANTHROPIC_API_KEY' in result

    @pytest.mark.asyncio
    async def test_browse_and_find_exception(self):
        """Test browse_and_find handles exceptions."""
        agent = WYN360Agent(api_key="test_key")

        with patch('wyn360_cli.agent.BrowserTaskExecutor') as MockExecutor:
            # Mock executor to raise exception
            MockExecutor.side_effect = Exception("Browser initialization failed")

            result = await agent.browse_and_find(
                ctx=None,
                task="Test task",
                url="https://example.com"
            )

            # Verify error message
            assert '❌' in result
            assert 'Error during autonomous browsing' in result
            assert 'Browser initialization failed' in result


class TestFormatHelpers:
    """Test formatting helper methods."""

    def test_format_extracted_data_simple(self):
        """Test formatting simple extracted data."""
        agent = WYN360Agent(api_key="test_key")

        data = {'price': '$99.99', 'title': 'Test Product'}
        result = agent._format_extracted_data(data)

        assert 'price' in result
        assert '$99.99' in result
        assert 'title' in result
        assert 'Test Product' in result

    def test_format_extracted_data_nested(self):
        """Test formatting nested extracted data."""
        agent = WYN360Agent(api_key="test_key")

        data = {
            'product': {
                'name': 'Sneakers',
                'price': '$99.99'
            },
            'shipping': {
                'speed': '2-day',
                'cost': 'Free'
            }
        }
        result = agent._format_extracted_data(data)

        assert 'product' in result
        assert 'Sneakers' in result
        assert '$99.99' in result
        assert 'shipping' in result

    def test_format_extracted_data_empty(self):
        """Test formatting empty extracted data."""
        agent = WYN360Agent(api_key="test_key")

        data = {}
        result = agent._format_extracted_data(data)

        assert 'No data extracted' in result

    def test_format_action_history(self):
        """Test formatting action history."""
        agent = WYN360Agent(api_key="test_key")

        history = [
            {
                'step': 1,
                'action': {'type': 'click', 'selector': '#search-btn'},
                'confidence': 80,
                'reasoning': 'Clicking the search button to start'
            },
            {
                'step': 2,
                'action': {'type': 'type', 'selector': '#search-box', 'text': 'sneakers'},
                'confidence': 90,
                'reasoning': 'Typing search query for sneakers'
            },
            {
                'step': 3,
                'action': {'type': 'navigate', 'url': 'https://example.com/results'},
                'confidence': 85,
                'reasoning': 'Navigating to results page'
            }
        ]

        result = agent._format_action_history(history)

        assert 'Step 1' in result
        assert 'CLICK' in result
        assert '80%' in result
        assert 'Target: #search-btn' in result

        assert 'Step 2' in result
        assert 'TYPE' in result
        assert 'Field: #search-box' in result

        assert 'Step 3' in result
        assert 'NAVIGATE' in result
        assert 'https://example.com/results' in result

    def test_format_action_history_empty(self):
        """Test formatting empty action history."""
        agent = WYN360Agent(api_key="test_key")

        history = []
        result = agent._format_action_history(history)

        assert 'No actions taken yet' in result

    def test_format_action_history_truncates(self):
        """Test that action history shows only last 5 actions."""
        agent = WYN360Agent(api_key="test_key")

        # Create 10 actions
        history = [
            {
                'step': i,
                'action': {'type': 'click'},
                'confidence': 80,
                'reasoning': f'Action {i}'
            }
            for i in range(1, 11)
        ]

        result = agent._format_action_history(history)

        # Should only show steps 6-10 (last 5)
        assert 'Step 6:' in result
        assert 'Step 10:' in result
        # Check that early steps are not present (use exact match with colon)
        assert 'Step 1:' not in result
        assert 'Step 2:' not in result
        assert 'Step 5:' not in result


class TestSystemPromptIntegration:
    """Test system prompt contains browse_and_find documentation."""

    def test_system_prompt_has_phase_5(self):
        """Test that system prompt includes Phase 5 autonomous browsing."""
        agent = WYN360Agent(api_key="test_key")
        prompt = agent._get_system_prompt()

        assert 'Phase 5' in prompt
        assert 'Autonomous' in prompt or 'autonomous' in prompt
        assert 'browse_and_find' in prompt

    def test_system_prompt_has_vision_requirement(self):
        """Test that system prompt mentions vision requirement."""
        agent = WYN360Agent(api_key="test_key")
        prompt = agent._get_system_prompt()

        assert 'vision' in prompt.lower() or 'Vision' in prompt
        assert 'Bedrock mode' in prompt or 'bedrock' in prompt.lower()

    def test_system_prompt_has_usage_examples(self):
        """Test that system prompt includes usage examples."""
        agent = WYN360Agent(api_key="test_key")
        prompt = agent._get_system_prompt()

        # Check for at least one example use case
        assert 'Amazon' in prompt or 'electronics' in prompt.lower() or 'cheapest' in prompt.lower()
