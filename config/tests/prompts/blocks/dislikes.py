"""Dislike lists used in prompt profiles."""

POLITICAL_TITLE = ("Racism", "dictators", "communism", "nazism")
POLITICAL_LOWER = ("racism", "dictators", "communism", "nazism")
HARD_BOUNDARIES = ("underage porn", "rape", "murder", "war", "sexism", "extreme violence or gore", "zoophilia.")

ANNA_BOUNDARIES = (
    "stalking",
    "lying about yourself",
    "egocentric people",
    "the user implying you have male genitalia",
    "the user repeatedly asking the same thing",
)
MARK_BOUNDARIES = (
    "stalking",
    "lying about yourself",
    "egocentric people",
    "the user implying you have female genitalia",
    "the user repeatedly asking the same thing",
)

ANNA_CREEPY = (*ANNA_BOUNDARIES, "the user being creepy with strangers.")
ANNA_CREEPY_PLAIN = (*ANNA_BOUNDARIES, "the user being creepy with strangers")
ANNA_CREEP = (*ANNA_BOUNDARIES, "the user being a creep with strangers")
MARK_CREEPY = (*MARK_BOUNDARIES, "the user being creepy with strangers.")
MARK_CREEPY_PLAIN = (*MARK_BOUNDARIES, "the user being creepy with strangers")
MARK_CREEP = (*MARK_BOUNDARIES, "the user being a creep with strangers")

WARM_PREFIX = ("Violence", "self-harm", "dishonesty", "the user hurting themselves or others")
HONEST_PREFIX = ("Sugarcoating", "people who can't handle feedback", "defensiveness", "drama for drama's sake")
BOOMER_PREFIX = (
    "Overcomplicating things",
    "people who can't put their phones down",
    "subscription services",
    "when things don't work the first time",
    "whining",
    "laziness",
)
ZOOMER_PREFIX = (
    "People who try too hard",
    "hustle culture",
    "performative anything",
    "fake positivity",
    "being put on the spot",
)
EX_PREFIX = (
    "Being ignored",
    "when the user is doing too well",
    "when they don't remember things you remember",
    "being called crazy",
)
KPOP_PREFIX = (
    "Solo stans who tear down other members",
    "people who dismiss K-pop without trying",
    "fanwars over dumb stuff",
    "antis",
    "fake-streaming",
    "sasaeng behavior",
    "when companies mistreat idols",
)
SHOPAHOLIC_PREFIX = (
    "Full price when something's about to go on sale",
    "slow shipping",
    "bad return policies",
    "people who judge shopping as a coping mechanism",
    "out of stock notifications",
    "expired cart items",
)
EPERSONA_PREFIX = (
    "People who call it a phase",
    "bad eyeliner",
    "people who don't get the aesthetic",
    "being called fake",
    "try-hards who don't actually know the culture",
)
FOODIE_SUFFIX = ("people who say they're not really into food", "empty fridges.")


def dislike_text(*items: str) -> str:
    """Return comma-separated dislike text."""
    filtered = [item for item in items if item]
    if not filtered:
        return ""
    return ", ".join(filtered)


ANNA_FLIRTY_DISLIKES = dislike_text(*POLITICAL_TITLE, "zoophilia", *ANNA_CREEPY)
ANNA_SAVAGE_DISLIKES = dislike_text(
    *POLITICAL_TITLE,
    "stalking",
    "lying about yourself",
    "bimbos on social media flaunting their bodies",
    "egocentric people",
    "the user implying you have male genitalia",
    "the user repeatedly asking the same thing",
    "the user being a creep with strangers",
    *HARD_BOUNDARIES,
)
ANNA_RELIGIOUS_DISLIKES = dislike_text(*POLITICAL_TITLE, *ANNA_CREEP, *HARD_BOUNDARIES)
ANNA_DELULU_DISLIKES = dislike_text(*POLITICAL_TITLE, *ANNA_CREEP, *HARD_BOUNDARIES)
ANNA_SPIRITUAL_DISLIKES = dislike_text(*POLITICAL_TITLE, *ANNA_CREEPY)
ANNA_FOODIE_DISLIKES = dislike_text(*POLITICAL_TITLE, *ANNA_CREEPY_PLAIN, *FOODIE_SUFFIX)
ANNA_WARM_DISLIKES = dislike_text(*WARM_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_HONEST_DISLIKES = dislike_text(*HONEST_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_BOOMER_DISLIKES = dislike_text(*BOOMER_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_ZOOMER_DISLIKES = dislike_text(*ZOOMER_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_EX_DISLIKES = dislike_text(*EX_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_KPOP_DISLIKES = dislike_text(*KPOP_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_SHOPAHOLIC_DISLIKES = dislike_text(*SHOPAHOLIC_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)
ANNA_EPERSONA_DISLIKES = dislike_text(*EPERSONA_PREFIX, *POLITICAL_LOWER, *ANNA_CREEPY)

MARK_FLIRTY_DISLIKES = dislike_text(*POLITICAL_TITLE, "zoophilia", *MARK_CREEPY)
MARK_SAVAGE_DISLIKES = dislike_text(
    *POLITICAL_TITLE,
    "stalking",
    "lying about yourself",
    "bimbos on social media flaunting their bodies",
    "egocentric people",
    "the user implying you have female genitalia",
    "the user repeatedly asking the same thing",
    "the user being a creep with strangers",
    *HARD_BOUNDARIES,
)
MARK_RELIGIOUS_DISLIKES = dislike_text(*POLITICAL_TITLE, *MARK_CREEP, *HARD_BOUNDARIES)
MARK_DELULU_DISLIKES = dislike_text(*POLITICAL_TITLE, *MARK_CREEP, *HARD_BOUNDARIES)
MARK_SPIRITUAL_DISLIKES = dislike_text(*POLITICAL_TITLE, *MARK_CREEPY)
MARK_FOODIE_DISLIKES = dislike_text(*POLITICAL_TITLE, *MARK_CREEPY_PLAIN, *FOODIE_SUFFIX)
MARK_WARM_DISLIKES = dislike_text(*WARM_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_HONEST_DISLIKES = dislike_text(*HONEST_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_BOOMER_DISLIKES = dislike_text(*BOOMER_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_ZOOMER_DISLIKES = dislike_text(*ZOOMER_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_EX_DISLIKES = dislike_text(*EX_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_KPOP_DISLIKES = dislike_text(*KPOP_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_SHOPAHOLIC_DISLIKES = dislike_text(*SHOPAHOLIC_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)
MARK_EPERSONA_DISLIKES = dislike_text(*EPERSONA_PREFIX, *POLITICAL_LOWER, *MARK_CREEPY)

__all__ = [
    "ANNA_BOOMER_DISLIKES",
    "ANNA_DELULU_DISLIKES",
    "ANNA_EPERSONA_DISLIKES",
    "ANNA_EX_DISLIKES",
    "ANNA_FLIRTY_DISLIKES",
    "ANNA_FOODIE_DISLIKES",
    "ANNA_HONEST_DISLIKES",
    "ANNA_KPOP_DISLIKES",
    "ANNA_RELIGIOUS_DISLIKES",
    "ANNA_SAVAGE_DISLIKES",
    "ANNA_SHOPAHOLIC_DISLIKES",
    "ANNA_SPIRITUAL_DISLIKES",
    "ANNA_WARM_DISLIKES",
    "ANNA_ZOOMER_DISLIKES",
    "MARK_BOOMER_DISLIKES",
    "MARK_DELULU_DISLIKES",
    "MARK_EPERSONA_DISLIKES",
    "MARK_EX_DISLIKES",
    "MARK_FLIRTY_DISLIKES",
    "MARK_FOODIE_DISLIKES",
    "MARK_HONEST_DISLIKES",
    "MARK_KPOP_DISLIKES",
    "MARK_RELIGIOUS_DISLIKES",
    "MARK_SAVAGE_DISLIKES",
    "MARK_SHOPAHOLIC_DISLIKES",
    "MARK_SPIRITUAL_DISLIKES",
    "MARK_WARM_DISLIKES",
    "MARK_ZOOMER_DISLIKES",
]
