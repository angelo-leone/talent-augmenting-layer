# Commercial use of Talent-Augmenting OS (TAOS)

The authoritative document is `LICENSE` (Business Source License 1.1). This file is a plain-language summary for procurement and security teams. Where this file disagrees with `LICENSE`, `LICENSE` wins.

## What you can do for free

If you are an organisation (company, public-sector body, academic institution, non-profit) and you want to use TAOS to assess, coach, augment, or support **your own people** (employees, contractors, members, students):

- You can clone the repo, modify it, and run it on your own infrastructure.
- You can use any of the TAOS install channels (universal system prompt, Custom GPT / Gemini Gem / Claude Project, MCP server, Desktop Extension, Cowork plugin, hosted web app, remote MCP endpoint).
- You can do this for **commercial purposes** inside your organisation. The licence's "Additional Use Grant" is explicitly designed to allow this.
- You do not need to contact the Licensor or purchase anything.

## What you cannot do for free

You may not provide the functionality of TAOS to third parties as a hosted or managed service. In practice this means you may not:

- Run a paid or unpaid SaaS that competes with the Licensor's hosted offering.
- Sell access to a TAOS-derived hosted assessment or coaching API.
- White-label TAOS and resell it under another brand.
- Operate a managed remote MCP endpoint that exposes TAOS functionality to third-party customers.

If you want to do any of the above, contact the Licensor (`angelo.leone1204@gmail.com`) for a separate commercial agreement.

## When the licence converts

On the **Change Date** (2030-04-30) or four years after a given version was first published, whichever is earlier, that version of TAOS converts to **Apache License 2.0**. From that point onwards, anyone (including competitors) may use that version commercially without restriction.

This means: every version you adopt today will eventually become open-source under Apache 2.0. The Business Source License is a four-year window during which the Licensor retains the right to monetise hosted services.

## Hosted service offered by the Licensor

The Licensor operates a hosted instance of TAOS at `https://proworker-hosted.onrender.com`. Use of that hosted service is governed by the deployment's Privacy Policy and (where applicable) a separate commercial subscription agreement. The BSL applies to the **source code** of TAOS; access to the Licensor's hosted instance is a separate commercial relationship.

## Frequently asked

**Q: Is BSL 1.1 an open-source licence?**
A: No, not by the OSI definition. It is "source-available" with a delayed open-source conversion. Many enterprise procurement teams now accept BSL 1.1 (e.g. it is the licence used by Sentry, Cockroach Labs, MariaDB MaxScale, and HashiCorp Terraform).

**Q: Can our employees inspect, audit, and modify the code?**
A: Yes. That is one of the reasons we picked BSL over a fully closed licence. Pilots routinely audit prompts, scoring algorithms, and data flows.

**Q: Can our security team review the source before we deploy?**
A: Yes. Clone the repo, audit it, run it through your SAST/DAST pipeline. We recommend you do.

**Q: Does internal use require attribution?**
A: You must keep the licence file conspicuously displayed on each copy or modified copy. You do not have to credit us in your end-user-facing UI when you self-host for internal purposes.

**Q: We want to fork TAOS for our internal needs. Allowed?**
A: Yes, as long as the fork is for your own internal use (not resold as a service to third parties) and the fork retains this licence on each copy.

**Q: When did the version we are running enter the BSL clock?**
A: Each version's Change Date is the earlier of (a) the explicit Change Date in `LICENSE` and (b) four years after that version was first publicly distributed. Check the LICENSE in the specific commit you are running.

## Contact

For commercial licence enquiries, security questions, DPA requests, or anything else: `angelo.leone1204@gmail.com`.
