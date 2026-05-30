"""
translate.py

Two-way translation layer — no IndicTransToolkit dependency.

- Indic languages: IndicTrans2 via HuggingFace transformers directly
- Classical langs (Sanskrit, Tibetan, Pali, Chinese): Ollama LLM fallback

The key difference from the IndicTransToolkit approach: we add the
required language tag tokens manually before the text, which is all
IndicTransToolkit's preprocess_batch() was doing anyway.

Usage:
    from src.translate import Translator
    t = Translator()
    english = t.to_english("न्यूटन का पहला नियम", src_lang="hin_Deva")
    hindi   = t.from_english("Newton's First Law", tgt_lang="hin_Deva")
"""

import os
import requests
import unicodedata
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# FLORES language codes for 22 scheduled Indian languages
# ---------------------------------------------------------------------------
INDIC_LANG_CODES = {
    "hindi":     "hin_Deva",
    "bengali":   "ben_Beng",
    "tamil":     "tam_Taml",
    "telugu":    "tel_Telu",
    "kannada":   "kan_Knda",
    "malayalam": "mal_Mlym",
    "marathi":   "mar_Deva",
    "gujarati":  "guj_Gujr",
    "punjabi":   "pan_Guru",
    "odia":      "ory_Orya",
    "assamese":  "asm_Beng",
    "urdu":      "urd_Arab",
    "english":   "eng_Latn",
}

# Classical / non-Indic: handled by Ollama LLM
CLASSICAL_LANGS = {"sanskrit", "tibetan", "pali", "chinese", "japanese", "korean"}

# Unicode block name fragment → FLORES code (for script detection)
SCRIPT_TO_LANG = {
    "DEVANAGARI": "hin_Deva",
    "BENGALI":    "ben_Beng",
    "TAMIL":      "tam_Taml",
    "TELUGU":     "tel_Telu",
    "KANNADA":    "kan_Knda",
    "MALAYALAM":  "mal_Mlym",
    "GURMUKHI":   "pan_Guru",
    "GUJARATI":   "guj_Gujr",
    "ORIYA":      "ory_Orya",
    "ARABIC":     "urd_Arab",
}


def detect_script(text: str) -> str | None:
    """Best-effort script detection via Unicode character names."""
    counts = {}
    for ch in text:
        try:
            name = unicodedata.name(ch)
            for script, code in SCRIPT_TO_LANG.items():
                if script in name:
                    counts[code] = counts.get(code, 0) + 1
        except ValueError:
            pass
    if not counts:
        return None
    return max(counts, key=counts.get)


class IndicTranslator:
    """
    IndicTrans2 translation without IndicTransToolkit.

    IndicTrans2 expects input in the format:
        <src_lang> <tgt_lang> sentence text here
    The model then generates the translation directly.
    This is equivalent to what IndicTransToolkit.preprocess_batch does.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._models = {}      # direction -> (model, tokenizer)

    def _load(self, direction: str):
        if direction in self._models:
            return self._models[direction]

        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        if direction == "indic_en":
            ckpt = os.getenv(
                "INDICTRANS2_INDIC_EN",
                "ai4bharat/indictrans2-indic-en-dist-200M"
            )
        else:
            ckpt = os.getenv(
                "INDICTRANS2_EN_INDIC",
                "ai4bharat/indictrans2-en-indic-dist-200M"
            )

        print(f"Loading IndicTrans2 ({direction}): {ckpt}  [first use only]")
        tokenizer = AutoTokenizer.from_pretrained(ckpt, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            ckpt, trust_remote_code=True
        ).to(self.device)
        self._models[direction] = (model, tokenizer)
        return model, tokenizer

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        direction = "indic_en" if tgt_lang == "eng_Latn" else "en_indic"
        model, tokenizer = self._load(direction)

        # IndicTrans2 expects language tags prepended to the input
        tagged = f"{src_lang} {tgt_lang} {text}"

        inputs = tokenizer(
            tagged,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        ).to(self.device)

        import torch
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_length=256,
                num_beams=4,
                early_stopping=True,
            )

        translated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return translated.strip()


class LLMTranslator:
    """Ollama-based fallback for Sanskrit, Tibetan, Pali, Chinese."""

    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def translate(self, text: str, src_lang: str, tgt_lang: str = "English") -> str:
        prompt = (
            f"Translate the following {src_lang} Buddhist/dharma term into {tgt_lang}. "
            f"Return only the translation, no explanation.\n\nTerm: {text}\nTranslation:"
        )
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()


class Translator:
    """
    Unified translation interface.
    Indic scripts  → IndicTrans2 (no IndicTransToolkit needed)
    Classical langs → Ollama LLM
    """

    def __init__(self, device: str = "cpu"):
        self._indic = None
        self._llm = None
        self.device = device

    @property
    def indic(self) -> IndicTranslator:
        if self._indic is None:
            self._indic = IndicTranslator(device=self.device)
        return self._indic

    @property
    def llm(self) -> LLMTranslator:
        if self._llm is None:
            self._llm = LLMTranslator()
        return self._llm

    def _is_classical(self, lang: str) -> bool:
        return lang.lower() in CLASSICAL_LANGS

    def to_english(self, text: str, src_lang: str) -> str:
        if self._is_classical(src_lang):
            return self.llm.translate(text, src_lang=src_lang, tgt_lang="English")
        return self.indic.translate(text, src_lang=src_lang, tgt_lang="eng_Latn")

    def from_english(self, text: str, tgt_lang: str) -> str:
        if self._is_classical(tgt_lang):
            return self.llm.translate(text, src_lang="English", tgt_lang=tgt_lang)
        return self.indic.translate(text, src_lang="eng_Latn", tgt_lang=tgt_lang)

    def detect_lang(self, text: str) -> str | None:
        return detect_script(text)
