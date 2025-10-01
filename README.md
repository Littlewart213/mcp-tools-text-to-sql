# Cookbook MCP TOOLS Text-to-SQL Playground

The `cookbook/` folder is our workshop bench for text-to-SQL ideas. While the
production service has to stay glued to hardened infrastructure, this space lets
us experiment, rehearse demos, and pressure-test new flows without risking live
systems. Each recipe mirrors the layout of the production code, so anything that
works here is already most of the way to shipping.

## Why we built text_to_sql

We kept getting the same request from analysts and operators: "Can I just ask a
question in plain English and get the data back?" Text_to_sql is our answer to
that ask. It removes the need for ad-hoc dashboards, shortens the time from idea
to insight, and gives us a safe proving ground to tune models and prompts before
they touch sensitive data sources.

## Working with the cookbook

- Pick the recipe that matches the scenario you want to explore.
- Skim the local README to understand the dataset, model assumptions, and
  suggested workflows.
- Run the provided commands or notebooks to walk through the end-to-end
  experience.
- Capture what you learn, tweak the configuration, and repeat until you are
  ready to promote the change.

Current recipe:

- `text_to_sql_demo/` – an AskDatabase-style environment backed by SQLite and a
  no-frills reranker, perfect for workshops or quick product walkthroughs.

If you need a step-by-step guide, head to `cookbook/text_to_sql_demo/README.md`.
That document holds the full demo instructions and troubleshooting notes, and
the underlying scripts are intentionally open for further development—extend the
flows, plug in new models, or swap data sources as your roadmap demands.
