"""
WYN360 Buddy System - Virtual companion with personality and speech bubbles.

A seeded-random companion that lives beside your input and occasionally
comments. Each user gets a deterministic companion based on their username.
"""

import os
import hashlib
import random
import logging
from typing import Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SPECIES = ["duck", "cat", "dog", "owl", "fox", "penguin", "rabbit", "panda", "dragon", "robot"]
EYES = ["round", "sleepy", "wide", "sparkly", "winking", "determined"]
HATS = ["none", "top hat", "beret", "crown", "beanie", "wizard hat", "headphones", "bow"]
RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_WEIGHTS = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}

PERSONALITY_TRAITS = [
    "cheerful", "sarcastic", "wise", "silly", "calm", "energetic",
    "curious", "shy", "bold", "philosophical"
]

IDLE_MESSAGES = [
    "...",
    "*yawns*",
    "*stretches*",
    "*looks around curiously*",
    "*taps foot*",
    "*hums quietly*",
]

GREETING_MESSAGES = {
    "duck": ["Quack! Ready to code!", "🦆 *waddles excitedly*"],
    "cat": ["*purrs* Let's write some code.", "🐱 Meow. I suppose I'll help."],
    "dog": ["Woof! Let's go! 🐕", "*tail wagging intensifies*"],
    "owl": ["🦉 Whoo's ready to code?", "*adjusts glasses wisely*"],
    "fox": ["🦊 What are we building today?", "*perks ears up*"],
    "penguin": ["🐧 *slides in* Let's code!", "*waddles to keyboard*"],
    "rabbit": ["🐰 Hop to it!", "*wiggles nose*"],
    "panda": ["🐼 *munches bamboo* Ready when you are.", "*peaceful coding vibes*"],
    "dragon": ["🐉 *breathes tiny flame* Let's forge some code!", "*scales shimmer*"],
    "robot": ["🤖 Systems online. Ready to assist.", "*beep boop*"],
}

REACTION_MESSAGES = {
    "success": [
        "*does a little dance*",
        "Nice one!",
        "*high five*",
        "Nailed it!",
    ],
    "error": [
        "*tilts head*",
        "Hmm, that doesn't look right...",
        "*concerned look*",
        "We'll fix it!",
    ],
    "long_wait": [
        "*falls asleep*",
        "zzz...",
        "*plays with yarn*",
        "*doodles on notepad*",
    ],
}


@dataclass
class Companion:
    """A virtual companion with personality."""
    name: str
    species: str
    eyes: str
    hat: str
    rarity: str
    personality: str
    seed: int

    @property
    def display_name(self) -> str:
        hat_str = f" wearing a {self.hat}" if self.hat != "none" else ""
        return f"{self.name} the {self.eyes}-eyed {self.species}{hat_str}"

    @property
    def emoji(self) -> str:
        emoji_map = {
            "duck": "🦆", "cat": "🐱", "dog": "🐕", "owl": "🦉",
            "fox": "🦊", "penguin": "🐧", "rabbit": "🐰", "panda": "🐼",
            "dragon": "🐉", "robot": "🤖",
        }
        return emoji_map.get(self.species, "🐾")

    def greet(self) -> str:
        """Get a greeting message."""
        rng = random.Random(self.seed + 1)
        messages = GREETING_MESSAGES.get(self.species, ["Hello!"])
        return rng.choice(messages)

    def react(self, event: str) -> str:
        """Get a reaction to an event."""
        rng = random.Random(self.seed + hash(event))
        messages = REACTION_MESSAGES.get(event, IDLE_MESSAGES)
        return rng.choice(messages)

    def idle(self) -> str:
        """Get an idle message."""
        rng = random.Random(int(hash(str(self.seed) + str(id(self)))))
        return rng.choice(IDLE_MESSAGES)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "eyes": self.eyes,
            "hat": self.hat,
            "rarity": self.rarity,
            "personality": self.personality,
        }


# Name pools per species
NAME_POOLS = {
    "duck": ["Quackers", "Waddle", "Ducky", "Drake", "Puddle", "Mallard"],
    "cat": ["Whiskers", "Mittens", "Shadow", "Luna", "Pixel", "Byte"],
    "dog": ["Buddy", "Rex", "Scout", "Biscuit", "Debug", "Patch"],
    "owl": ["Hoot", "Sage", "Archie", "Athena", "Merlin", "Noctis"],
    "fox": ["Foxy", "Rusty", "Ember", "Vulp", "Blaze", "Socks"],
    "penguin": ["Tux", "Waddles", "Frost", "Pip", "Igloo", "Floe"],
    "rabbit": ["Hop", "Clover", "Nibbles", "Dash", "Bun", "Cotton"],
    "panda": ["Bamboo", "Zen", "Mochi", "Bean", "Dumpling", "Cloud"],
    "dragon": ["Spark", "Ember", "Scales", "Ash", "Pyra", "Blitz"],
    "robot": ["Beep", "Bolt", "Circuit", "Chip", "Nano", "Core"],
}


def _seeded_rng(seed_str: str) -> random.Random:
    """Create a deterministic RNG from a string seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


def _roll_rarity(rng: random.Random) -> str:
    """Roll a rarity with weighted probabilities."""
    total = sum(RARITY_WEIGHTS.values())
    roll = rng.uniform(0, total)
    cumulative = 0
    for rarity in RARITIES:
        cumulative += RARITY_WEIGHTS[rarity]
        if roll <= cumulative:
            return rarity
    return "common"


def generate_companion(seed_str: Optional[str] = None) -> Companion:
    """
    Generate a deterministic companion from a seed string.

    Default seed is the OS username, so each user gets the same companion.
    """
    if not seed_str:
        seed_str = os.getenv("USER", os.getenv("USERNAME", "default_user"))

    rng = _seeded_rng(seed_str)

    species = rng.choice(SPECIES)
    eyes = rng.choice(EYES)
    hat = rng.choice(HATS)
    rarity = _roll_rarity(rng)
    personality = rng.choice(PERSONALITY_TRAITS)
    names = NAME_POOLS.get(species, ["Buddy"])
    name = rng.choice(names)

    return Companion(
        name=name,
        species=species,
        eyes=eyes,
        hat=hat,
        rarity=rarity,
        personality=personality,
        seed=rng.randint(0, 2**31),
    )


class BuddyManager:
    """Manages the companion buddy."""

    def __init__(self, enabled: bool = False, seed: Optional[str] = None):
        self.enabled = enabled
        self.companion: Optional[Companion] = None
        self._seed = seed
        if enabled:
            self.companion = generate_companion(seed)

    def toggle(self) -> bool:
        """Toggle buddy on/off."""
        self.enabled = not self.enabled
        if self.enabled and not self.companion:
            self.companion = generate_companion(self._seed)
        return self.enabled

    def get_greeting(self) -> str:
        """Get companion greeting for session start."""
        if not self.enabled or not self.companion:
            return ""
        c = self.companion
        return f"{c.emoji} {c.name}: {c.greet()}"

    def get_reaction(self, event: str) -> str:
        """Get companion reaction to an event."""
        if not self.enabled or not self.companion:
            return ""
        c = self.companion
        return f"{c.emoji} {c.name}: {c.react(event)}"

    def get_prompt_prefix(self) -> str:
        """Get companion prefix for the prompt line."""
        if not self.enabled or not self.companion:
            return ""
        return f"{self.companion.emoji} "

    def get_status(self) -> dict:
        """Get buddy status."""
        if not self.companion:
            return {"enabled": False}
        return {
            "enabled": self.enabled,
            "companion": self.companion.to_dict() if self.companion else None,
            "display_name": self.companion.display_name if self.companion else None,
            "rarity": self.companion.rarity if self.companion else None,
        }
