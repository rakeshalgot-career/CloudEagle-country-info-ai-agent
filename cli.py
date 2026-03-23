from __future__ import annotations

from country_agent.service import CountryInfoAgent


def main() -> None:
    agent = CountryInfoAgent()
    print("Country Info AI Agent")
    print("Type 'exit' to quit.")

    while True:
        question = input("\nAsk: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        answer = agent.ask(question)
        print(f"\n{answer}")


if __name__ == "__main__":
    main()
