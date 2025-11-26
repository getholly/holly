import enum


class LLMModel(str, enum.Enum):
    GPT_4o = "gpt-4o"
    LLAMA3_3 = "llama3.3:latest"
    MISTRAL7B = "mistral7b"
    GEMINI_2_5 = "gemini-2.5-pro-exp-03-25"
    GEMINI_2 = "gemini-2.0-flash-exp"
    GEMINI_2_FLASH = "gemini-2.0-flash"
    GEMINI_2_FLASH_THINKING = "gemini-2.0-flash-thinking-exp-01-21"
    GEMINI_2_PRO_EXP = "gemini-2.0-pro-exp-02-05"
    GEMINI_1_5 = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-flash-pro"
    CLAUDE_SONNET = "claude-3-7-sonnet"
