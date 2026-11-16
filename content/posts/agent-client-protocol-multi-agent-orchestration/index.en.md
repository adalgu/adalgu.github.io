---
title: "Don't Build Agents, Connect Them — How ACP Is Changing Multi-Agent Orchestration"
description: "Agent-in-Agent vs. ACP (Agent Client Protocol) — two approaches to multi-agent orchestration"
draft: false
translationKey: "agent-client-protocol-multi-agent-orchestration"
url: "/en/posts/agent-client-protocol-multi-agent-orchestration/"
author: Gunn Kim
cover:
  alt: "Cover image for \"Don't Build Agents, Connect Them — How ACP Is Changing Multi-Agent Orchestration\""
  hiddenInList: false
  hiddenInSingle: false
  image: https://i.imgur.com/qHiosRH.jpeg
date: '2026-03-02'
keywords: &id001
- AI
- agent
- ACP
- multi-agent
lastmod: '2026-03-02T01:32:00.000Z'
notion_id: 3177522e-eb2f-8178-9c13-c49638317336
slug: "agent-client-protocol-multi-agent-orchestration"
tags:
- AI
- agent
- ACP
- multi-agent
---
![AI agent network — generated with Gemini 3 Pro](https://i.imgur.com/qHiosRH.jpeg)

## Anatomy of ACP

### a) What Is a Protocol?

A lot of people's eyes glaze over the moment the word "protocol" comes up. Developers do it too, and non-developers even more so. So let me start by unpacking the word in everyday language.

A protocol is **an agreed-upon way of having a conversation**.

Think about parcel delivery. The sender puts the item in a box, writes the address, and pays the shipping fee. The recipient tracks it by waybill number, signs, and takes delivery. That procedure is nearly identical no matter which courier in the country you use. That's a protocol. What if every courier had its own box sizes, its own way of writing addresses, its own pickup procedure? You'd have to learn a different method for each courier just to send something. Chaos.

The internet works the way it does thanks to a protocol called **HTTP**. Whether the server belongs to Naver (네이버, Korea's largest web portal), Google, or Kakao (카카오, the company behind Korea's dominant messenger), a web browser sends requests and receives responses in exactly the same way. It doesn't matter what language the server was written in or what operating system it runs on. Everything connects because there's a common language called HTTP.

Before HTTP came along, web servers and browsers each communicated in their own way. There was no standard. Once HTTP unified all of that, the web grew explosively. **A single standard changed the entire ecosystem.**

### b) Why Agents Need a Protocol

The world of AI agents right now looks a lot like the web before HTTP.

Claude Code does things the Claude Code way. OpenAI Codex uses a different API and input format. Google's Gemini CLI is different again. How you launch it, what the input looks like, how you parse the output, how you handle errors — it's different for every agent.

So an idea like "I want to use Claude Code and Codex together, with one writing the code and the other reviewing it" sounds simple, but actually implementing it is complicated. You have to learn how each agent runs, parse its output, handle its errors, and write the lifecycle-management code yourself.

This is exactly where **ACP (Agent Client Protocol)** comes in.

ACP is a protocol that connects different coding agents through a **standardized interface**. Claude Code, Codex, OpenCode, Gemini CLI — go through ACP and you can handle them all the same way. From the orchestrator's point of view, there's no need to know "which agent this is." You just call it via ACP.

Just as HTTP let you use the web without knowing "which server this is."

### c) ACP's Core Design Principles

Once you understand how ACP is designed, you can see why this approach is so powerful. It comes down to three things.

**Isolation.** Each agent session runs as an independent process. If agent A runs amok or gets stuck in an infinite loop, agent B and the main orchestrator are unaffected. It's like browser tabs each running independently, so that when one crashes the others stay alive.

**Standardization.** Spawning sessions, passing messages, receiving results, handling errors — all of it follows the same interface for every agent. Swap out an agent and you don't have to change your orchestration logic.

**Lifecycle Management.** A TTL (Time-To-Live) setting shuts agent sessions down automatically. Thread binding lets you attach an agent to a particular conversational context. Model overrides let you run the same agent with a different model. Because these lifecycle concerns are handled at the protocol level, the user only has to focus on the "business logic."

### d) How It Relates to (and Differs from) MCP

MCP (Model Context Protocol) gets mentioned a lot these days too. MCP and ACP look similar, but they solve different problems.

**MCP is a protocol for "giving tools to a model."** It connects web search tools, file system tools, and database tools in a standardized way so that an LLM can use them. The model is the protagonist, and tools are a means of extending the model's capabilities.

**ACP is a protocol for "connecting agents to agents."** It lets another agent or an orchestrator call and manage already-finished agents (Claude Code, Codex, and so on) in a standard way. The orchestrator is the protagonist, and each agent is an independent actor.

Put simply: MCP is "model + tools," and ACP is "agent + agent."

If MCP "gave the model arms and legs," ACP is the protocol that "lets those agents, now equipped with arms and legs, work as a team." The two aren't competitors; they're complementary standards operating at different layers.

---

## Agent-in-Agent vs Agent-via-Protocol: A Difference in Philosophy

Now for the central contrast. The difference between these two approaches isn't merely a matter of technical choice. It's **a difference in philosophy**.

### Melanie Li's Experiment: The "Build It Yourself" Approach

AI engineer Melanie Li shared what it was like to build a multi-agent system. Here's the summary.

Li built the sub-agents directly with the OpenAI Agent SDK, defining a coding agent, a review agent, and a test agent each in code and hand-writing the communication logic, state management, and error handling between them.

The result? **3x the latency, 3–5x the cost, and debugging hell.**

Why did this happen? When an agent creates and manages other agents "from the inside," every layer adds more LLM calls. Tokens get spent when the orchestrator explains the task to a sub-agent, and more tokens get spent interpreting the sub-agent's result. As the layers stack up, the complexity multiplies.

The more serious problem is debugging. It's extremely hard to trace exactly what instruction agent A gave agent B, or how B interpreted that instruction. Because everything happens inside the LLM's context, the debugging tools of traditional programming don't work.

This is the inherent limit of the "Agent-in-Agent" approach. **The attempt to build agents ends up eating away at the agents' capabilities.**

### ACP's Approach: The "Connect Them" Approach

ACP's philosophy starts from the exact opposite end.

**Don't build agents that already work — connect them.**

Claude Code is already an outstanding coding agent. So is Codex. So is OpenCode. These are finished agents that have already been through months or years of development and fine-tuning. Trying to "rebuild them inside my own agent system" is a losing battle from the start.

Instead, ACP takes this approach: run each agent as an independent process, and exchange messages through a standardized interface. The orchestrator doesn't need to know anything about an agent's internals. It just routes: "this task goes to Claude Code, that one goes to Codex."

Here's an analogy. Agent-in-Agent is "training employees myself so they do everything my way." ACP is "contracting freelancers who are already experts in their field, project by project." The former gives you a sense of control, but the cost and time are enormous. The latter feels unfamiliar at first, but you get to use the experts' skills exactly as they are.

**The key difference in one line**: Agent-in-Agent "reimplements an agent's capabilities in code," while ACP "borrows an agent's capabilities through a protocol."

<!-- notion-table: column_header=true row_header=true -->
| Agent-in-Agent   | Agent-via-Protocol (ACP)   |
|:-----------------|:---------------------------|
| **Approach**           | Reimplement agents in code              |
| **Latency**         | Extra LLM calls at every layer            |
| **Cost**           | 3–5x orchestration overhead          |
| **Debugging**          | Inside the LLM context, hard to trace        |
| **Agent quality**      | LLM imitates the role                 |
| **Codebase**        | Large amounts of custom code on top of an SDK          |

---

## In Practice: How I Actually Use It

Concepts alone aren't enough. Let me share how I actually use this.

### Case 1: A 12-Hour Autonomous Development Cron

Every night at midnight, a cron job runs. It reads the GitHub issues that carry a label and, for each issue, spawns a Claude Code session through ACP. Claude Code writes the code, opens a PR, and ends the session. Because a TTL is set, no matter how long it takes, the session shuts down automatically once the specified time has passed.

All of this runs on a few dozen lines of config. If I'd implemented the same thing with the Agent SDK? Session management code, retry logic, error handling, timeout management... the codebase would have been three times bigger.

### Case 2: Multi-Agent Code Review

When a PR goes up, two agents review it in sequence. First Codex analyzes code quality and potential bugs; then Claude Code takes those results and re-reviews from an architectural perspective. The two agents run as separate, independent processes, and ACP relays the results.

If I'd implemented this the Agent-in-Agent way, the orchestrator agent would have to alternate between playing "the Codex role" and "the Claude Code role." In the end that's a single LLM imitating two roles, and the real strengths of each specialized agent disappear.

With ACP, Codex is the real Codex and Claude Code is the real Claude Code.

### Case 3: Thread-Bound Coding Sessions

When I say "implement this feature" in a Slack thread, an OpenCode session bound to that thread is created. From then on, every exchange in that thread is connected to that session. The context is preserved. Until the session is closed, it remembers the earlier conversation.

This is possible thanks to ACP's thread binding feature. Link the session ID to the thread ID, and the ACP runtime handles the message routing on its own. I wrote almost no code.

---

## The Insight: Raise the Level of Abstraction

Here's the core insight I took away from these experiences.

**Complexity always comes from the wrong level of abstraction.**

When building multi-agent systems, a lot of people think at the "LLM level." What prompt to use, how to define the agent's role, how to pass context along. Implement multi-agent at this level and you end up where Melanie Li did.

ACP raises the level of abstraction a notch. You think not at the level of the LLM but at the level of the **agent process**. Each agent is an independent unit of execution, and the protocol is the infrastructure that connects them. The orchestrator only has to decide "which agent gets which task," not "which model to use."

This also ties into a classic principle of software engineering: Separation of Concerns. The orchestrator decides "what to do," ACP handles "how to connect," and the individual agents take care of "how to actually do it."

**If MCP "extended the model's capabilities," ACP "makes collaboration between agents possible."**

Thanks to MCP, LLMs became able to search the web, read files, and run code. The next step is for these agents with their extended capabilities to collaborate with one another. ACP is that layer. If MCP created a "tool ecosystem," ACP is the protocol that creates an "agent ecosystem."

HTTP → REST → the explosive growth of the web ecosystem. That resembles the flow from MCP → ACP → the agent ecosystem.

---

## Wrapping Up: Don't Build, Connect

When you first encounter AI agents, you get the urge to "build one myself." The urge to define in code an agent that behaves exactly the way you want, and to control everything. I get it. I was the same.

But there's something I came to realize through real-world work. Trying to "rebuild my own way" agents that top experts have spent years refining returns very little for the cost and time involved.

Just as HTTP unified the web, ACP could become the standard for agent orchestration. It's still early days, but the direction is clear. From an era of building agents to an era of connecting them.

I still vividly remember how it felt the first time I orchestrated Claude Code, Codex, and OpenCode with a few lines of config. That feeling of "Wait, it was this easy?" That simplicity is itself the proof of the right abstraction.

Making complicated things complicated is easy. Making complicated things simple is real engineering.

---

*The real-world cases in this post are based on the OpenClaw ACP runtime. I plan to cover the official ACP documentation and my experiment results in a separate post.*
