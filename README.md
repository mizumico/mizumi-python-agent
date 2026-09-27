# Mizumi Python Agent

> A ~100-line tool-calling agent loop in pure Python, powered by [Mizumi](https://mizumi.co) — one OpenAI-compatible API for OpenAI & Gemini models. Only dependency: the `openai` package.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/mizumico/mizumi-python-agent/pulls)

## What it does

`agent.py` implements the classic agent loop: send messages to the model, execute any `tool_calls` it requests, feed results back, and repeat until the model returns a final answer. Two demo tools are included:

- **`calculator`** — safely evaluates math expressions (`ast`-based, no `eval` of arbitrary code)
- **`get_current_time`** — returns the current local time

Python >= 3.9, no framework, no magic — read the file top to bottom and you'll understand the whole pattern.

## Get started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export MIZUMI_API_KEY=sk-your-key        # get one at https://mizumi.co ($3 free trial credit)
# optional: export MIZUMI_MODEL=gpt-5.6-luna   # default is the budget tier

python agent.py "What is (128 * 46) + 7, and what time is it right now?"
```

Tip: `cp .env.example .env`, fill it in, then `source .env` — or use any env loader you like.

## Demo output

```text
Model: gpt-5.6-luna
You:   What is (128 * 46) + 7, and what time is it right now?

  [round 1] tool call: calculator({'expression': '(128 * 46) + 7'})
  [round 1] tool result: 5895
  [round 1] tool call: get_current_time({})
  [round 1] tool result: 2025-07-08T14:32:10+08:00

Agent: (128 × 46) + 7 = 5,895. The current local time is 2025-07-08 14:32:10 (UTC+8).
```

## Add your own tool

Three small steps — search for these in `agent.py`:

1. **Implement a Python function** that returns a string:

   ```python
   def get_weather(city: str) -> str:
       ...  # call your API here
       return f"Sunny, 27°C in {city}"
   ```

2. **Describe it in `TOOLS`** (this is the JSON Schema the model sees):

   ```python
   {
       "type": "function",
       "function": {
           "name": "get_weather",
           "description": "Get the current weather for a city.",
           "parameters": {
               "type": "object",
               "properties": {
                   "city": {"type": "string", "description": "City name, e.g. 'Tokyo'."}
               },
               "required": ["city"],
           },
       },
   },
   ```

3. **Register it in `TOOL_DISPATCH`** so the loop can execute it:

   ```python
   TOOL_DISPATCH["get_weather"] = lambda args: get_weather(args["city"])
   ```

That's it — the `while`-style loop in `run_agent()` handles the rest.

## Models & docs

Default model is `gpt-5.6-luna` (budget tier). Any model from Mizumi works — OpenAI and Gemini families alike — via `MIZUMI_MODEL`. Full list and pricing: **[mizumi.co](https://mizumi.co)** · API docs: **[mizumi.co/docs](https://mizumi.co/docs)**

## License

MIT — see [LICENSE](LICENSE).

---

Built with Mizumi — official OpenAI & Gemini models via one OpenAI-compatible API. $3 free trial credit at https://mizumi.co
