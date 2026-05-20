
import re


class Reader:
    PARAGRAPH_BREAK_TOKEN = "__PARA_BREAK__"

    def __init__(self):
        self.words = []
        self.index = 0

        self.soft_break_words = {
            "and", "or", "but", "the", "a", "an",
            "to", "of", "in", "on", "at", "for", "with",
            "by", "as", "if", "into", "than", "that",
            "is", "was", "were", "be", "been"
        }

        self.preposition_starters = {
            "of", "in", "on", "at", "to", "for", "with",
            "by", "from", "into", "over", "under", "through",
            "between", "against", "during", "without", "before",
            "after", "around", "near"
        }

    def load_text(self, text: str):
        self.words = self._tokenize_text(text)
        self.index = 0

    def load_text_with_index(self, text: str, word_index: int = 0):
        self.words = self._tokenize_text(text)
        self.index = max(0, min(word_index, len(self.words)))

    def _tokenize_text(self, text: str):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n\s*\n+", f" {self.PARAGRAPH_BREAK_TOKEN} ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", " ", text)
        text = text.strip()

        if not text:
            return []

        return text.split(" ")

    def get_next_chunk(self, chunk_size: int = 1, punctuation_slowdown: bool = True):
        if self.index >= len(self.words):
            return None, 1.0, 0.0

        current = self.words[self.index]

        # Paragraph break should display nothing new, but create a pause.
        if current == self.PARAGRAPH_BREAK_TOKEN:
            self.index += 1
            return "", 2.6, 0.35

        if chunk_size <= 1:
            chunk_words = [current]
            self.index += 1
        else:
            chunk_words = self._get_smart_chunk(chunk_size)

        visible_words = [w for w in chunk_words if w != self.PARAGRAPH_BREAK_TOKEN]
        chunk_text = " ".join(visible_words)

        punctuation_multiplier = self._get_delay_multiplier(chunk_text, punctuation_slowdown)
        reading_units = self._get_chunk_reading_units(visible_words)

        # Mild extra pause if a paragraph token was included in the chunk
        if self.PARAGRAPH_BREAK_TOKEN in chunk_words:
            punctuation_multiplier = max(punctuation_multiplier, 1.6)

        return chunk_text, punctuation_multiplier, reading_units

    def _get_smart_chunk(self, chunk_size: int):
        start = self.index
        end = start
        chunk = []

        while end < len(self.words) and len([w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN]) < chunk_size:
            word = self.words[end]

            # Stop before a paragraph break if we already have visible words.
            if word == self.PARAGRAPH_BREAK_TOKEN and chunk:
                break

            chunk.append(word)
            end += 1

            # If a paragraph token somehow enters first, keep it isolated.
            if word == self.PARAGRAPH_BREAK_TOKEN:
                break

        if not chunk:
            chunk = [self.words[start]]
            end = start + 1

        visible_chunk = [w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN]

        if len(visible_chunk) > 1:
            last_word = self._normalize_word(visible_chunk[-1])

            if last_word in self.soft_break_words and len(visible_chunk) >= 3:
                # Trim one visible trailing connector
                for i in range(len(chunk) - 1, -1, -1):
                    if chunk[i] != self.PARAGRAPH_BREAK_TOKEN:
                        del chunk[i]
                        end -= 1
                        break

            while len([w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN]) > 1:
                last_visible = self._last_visible_word(chunk)
                if last_visible and self._ends_with_opening_wrapper(last_visible):
                    for i in range(len(chunk) - 1, -1, -1):
                        if chunk[i] != self.PARAGRAPH_BREAK_TOKEN:
                            del chunk[i]
                            end -= 1
                            break
                else:
                    break

            visible_chunk = [w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN]

            if len(visible_chunk) >= 2 and end < len(self.words):
                last_clean = self._normalize_word(visible_chunk[-1])

                next_word = self.words[end]
                while next_word == self.PARAGRAPH_BREAK_TOKEN and end + 1 < len(self.words):
                    next_word = self.words[end + 1]

                next_clean = self._normalize_word(next_word)

                if last_clean in self.preposition_starters and next_clean:
                    if len(visible_chunk) >= 3:
                        for i in range(len(chunk) - 1, -1, -1):
                            if chunk[i] != self.PARAGRAPH_BREAK_TOKEN:
                                del chunk[i]
                                end -= 1
                                break

            visible_joined = " ".join([w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN])
            if visible_joined.count('"') % 2 == 1 and len([w for w in chunk if w != self.PARAGRAPH_BREAK_TOKEN]) >= 3:
                for i in range(len(chunk) - 1, -1, -1):
                    if chunk[i] != self.PARAGRAPH_BREAK_TOKEN:
                        del chunk[i]
                        end -= 1
                        break

        if not chunk:
            chunk = [self.words[start]]
            end = start + 1

        self.index = end
        return chunk

    def _last_visible_word(self, chunk):
        for word in reversed(chunk):
            if word != self.PARAGRAPH_BREAK_TOKEN:
                return word
        return ""

    def _normalize_word(self, word: str):
        if word == self.PARAGRAPH_BREAK_TOKEN:
            return ""
        return word.strip().lower().strip("\"'“”‘’()[]{}.,;:!?")

    def _ends_with_opening_wrapper(self, word: str):
        stripped = word.strip()
        return stripped.endswith(("(", "[", "{", "“", "\"", "—", "--"))

    def _strip_trailing_wrappers(self, text: str):
        trailing_wrappers = "\"'”’)]}"
        while text and text[-1] in trailing_wrappers:
            text = text[:-1].rstrip()
        return text

    def _get_delay_multiplier(self, chunk_text: str, punctuation_slowdown: bool):
        if not punctuation_slowdown:
            return 1.0

        text = chunk_text.strip()
        if not text:
            return 1.0

        clean_end = self._strip_trailing_wrappers(text)
        if not clean_end:
            return 1.0

        multiplier = 1.0

        if clean_end.endswith(("...", "…")):
            multiplier = 2.25
        elif clean_end.endswith((".", "!", "?")):
            multiplier = 1.85
        elif clean_end.endswith((";", ":")):
            multiplier = 1.40
        elif clean_end.endswith(","):
            multiplier = 1.20

        internal_text = clean_end[:-1] if len(clean_end) > 1 else ""

        if "," in internal_text:
            multiplier = max(multiplier, 1.08)
        if ";" in internal_text or ":" in internal_text:
            multiplier = max(multiplier, 1.12)
        if "(" in text or ")" in text:
            multiplier = max(multiplier, 1.08)
        if "—" in text or "--" in text:
            multiplier = max(multiplier, 1.10)

        return multiplier

    def _get_chunk_reading_units(self, chunk_words):
        if not chunk_words:
            return 0.35

        total = 0.0
        for word in chunk_words:
            total += self._get_word_reading_weight(word)
        return max(total, 1.0)

    def _get_word_reading_weight(self, word: str):
        original = word.strip()
        if not original:
            return 0.0

        clean = self._normalize_word(original)

        if not clean:
            return 0.6

        weight = 1.0

        length = len(clean)
        if length <= 2:
            weight = 0.85
        elif length <= 4:
            weight = 1.0
        elif length <= 7:
            weight = 1.12
        elif length <= 10:
            weight = 1.28
        elif length <= 14:
            weight = 1.48
        else:
            weight = 1.68

        hyphen_count = original.count("-")
        if hyphen_count > 0:
            weight += 0.18 * hyphen_count

        slash_count = original.count("/")
        if slash_count > 0:
            weight += 0.12 * slash_count

        if "'" in clean or "’" in original:
            weight += 0.05

        if clean.isupper() and len(clean) > 1:
            weight += 0.12

        if any(ch.isdigit() for ch in original):
            weight += 0.18

        if original[0] in "\"'“‘([":
            weight += 0.05
        if original[-1] in "\"'”’)]}":
            weight += 0.05

        internal_punct = 0
        for ch in original:
            if ch in ",;:!?":
                internal_punct += 1
        if internal_punct:
            weight += min(0.18, internal_punct * 0.06)

        return max(weight, 0.7)

    def step_back(self, amount: int = 10):
        self.index = max(0, self.index - amount)

    def reset(self):
        self.index = 0

    def set_index(self, index: int):
        self.index = max(0, min(index, len(self.words)))

    def get_index(self) -> int:
        return self.index

    def is_finished(self) -> bool:
        return self.index >= len(self.words)

    def get_progress(self) -> int:
        visible_words = [w for w in self.words if w != self.PARAGRAPH_BREAK_TOKEN]
        if not visible_words:
            return 0

        visible_index = len([w for w in self.words[:self.index] if w != self.PARAGRAPH_BREAK_TOKEN])
        return int((visible_index / len(visible_words)) * 100)

    def has_text(self) -> bool:
        return len(self.words) > 0