"""Minimal tool-calling agent loop powered by Mizumi (OpenAI-compatible API).

Run:
    export MIZUMI_API_KEY=sk-...
    python agent.py "What is (128 * 46) + 7, and what time is it right now?"

The agent keeps calling tools until the model produces a final answer.
Only dependency: the `openai` package.
"""

import ast
import datetime
import json
import os
import sys

from openai import OpenAI

# Mizumi is OpenAI-compatible: just change base_url. Docs: https://mizumi.co/docs
client = OpenAI(
    api_key=os.environ["MIZUMI_API_KEY"],
    base_url="https://api.mizumi.co/v1",
)

# gpt-5.6-luna is the budget tier; override with MIZUMI_MODEL if you like.
MODEL = os.environ.get("MIZUMI_MODEL", "gpt-5.6-luna")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def calculator(expression: str) -> str:
    """Evaluate a basic math expression safely (numbers and +-*/() only)."""
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.FloorDiv,
    )
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"Disallowed syntax in expression: {expression!r}")
    result = eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}})
    return str(result)


def get_current_time() -> str:
    """Return the current local date and time in ISO 8601 format."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a math expression like '(128 * 46) + 7'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A math expression using numbers and +-*/() operators.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_DISPATCH = {
    "calculator": lambda args: calculator(args["expression"]),
    "get_current_time": lambda args: get_current_time(),
}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def run_agent(user_message: str, max_rounds: int = 10) -> str:
    """Loop: call the model, execute any tool calls, repeat until final answer."""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use tools when they help.",
        },
        {"role": "user", "content": user_message},
    ]

    for round_num in range(1, max_rounds + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        messages.append(message)

        # No tool calls -> we have the final answer.
        if not message.tool_calls:
            return message.content or ""

        # Execute each requested tool and feed results back to the model.
        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"  [round {round_num}] tool call: {name}({args})")
            handler = TOOL_DISPATCH.get(name)
            try:
                result = handler(args) if handler else f"Unknown tool: {name}"
            except Exception as exc:  # surface errors to the model so it can recover
                result = f"Error: {exc}"
            print(f"  [round {round_num}] tool result: {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    return "Stopped: reached the maximum number of tool-call rounds."


def main() -> None:
    if not os.environ.get("MIZUMI_API_KEY"):
        sys.exit(
            "MIZUMI_API_KEY is not set. Get a key at https://mizumi.co "
            "($3 free trial credit for new users) and export it first."
        )

    prompt = " ".join(sys.argv[1:]) or (
        "What is (128 * 46) + 7, and what time is it right now?"
    )
    print(f"Model: {MODEL}")
    print(f"You:   {prompt}\n")
    answer = run_agent(prompt)
    print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
