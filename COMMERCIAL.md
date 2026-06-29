# Commercial use of Talent-Augmenting OS (TAOS)

The authoritative document is `LICENSE` (Business Source License 1.1). This file is a plain-language summary for procurement and security teams. Where this file disagrees with `LICENSE`, `LICENSE` wins.

## What you can do for free

**As an individual**, you can use TAOS for your own work at no cost, including adapting the universal prompt files for use with a third-party AI assistant, whether or not your work benefits an employer or client. You do not need to contact us or buy anything.

**As an organisation**, you can evaluate, audit, and build with TAOS at no cost, as long as the use is **non-production**:

- Clone the repo, read it, modify it, and run it on your own infrastructure for evaluation, security review, testing, and development.
- Put it through your SAST/DAST pipeline and have your security team inspect every prompt, scoring algorithm, and data flow before you decide to deploy.
- Run a non-production pilot to decide whether TAOS is right for your people.

"Non-production use" means use that is not part of running your live operations: trying it, auditing it, or building on it in a development environment.

## What needs a commercial licence

You need a commercial licence once TAOS is deployed for an organisation or provided to other people, rather than used by one individual for their own work. This includes:

- An organisation deploying TAOS (hosted or self-hosted) to assess, coach, augment, or support its people (employees, contractors, members, students), whether or not anyone is charged.
- Running TAOS, or a fork of it, as part of an organisation's infrastructure.
- Providing the functionality of TAOS to other people as a hosted or managed service: a paid or unpaid SaaS, a TAOS-derived hosted assessment or coaching API, a white-labelled resale, or a managed remote MCP endpoint exposing TAOS to third-party customers.

Both internal self-hosting and third-party hosted/managed services are available under commercial terms. Contact the Licensor (`angelo.leone1204@gmail.com`) to arrange one.

## When the licence converts

On the **Change Date** (2030-04-30) or four years after a given version was first published, whichever is earlier, that version of TAOS converts to **Apache License 2.0**. From that point onwards, anyone (including competitors) may use that version commercially without restriction.

This means: every version you adopt today will eventually become open-source under Apache 2.0. The Business Source License is a four-year window during which the Licensor retains the right to monetise organisational and hosted deployments of the work, including internal self-hosting.

## Hosted service offered by the Licensor

The Licensor operates a hosted instance of TAOS at `https://proworker-hosted.onrender.com`. Use of that hosted service is governed by the deployment's Privacy Policy and (where applicable) a separate commercial subscription agreement. The BSL applies to the **source code** of TAOS; access to the Licensor's hosted instance is a separate commercial relationship.

## Frequently asked

**Q: Is BSL 1.1 an open-source licence?**
A: No, not by the OSI definition. It is "source-available" with a delayed open-source conversion. Many enterprise procurement teams now accept BSL 1.1 (e.g. it is the licence used by Sentry, Cockroach Labs, MariaDB MaxScale, and HashiCorp Terraform).

**Q: Can our employees inspect, audit, and modify the code?**
A: Yes. That is one of the reasons we picked BSL over a fully closed licence. Pilots routinely audit prompts, scoring algorithms, and data flows.

**Q: Can our security team review the source before we deploy?**
A: Yes. Clone the repo, audit it, run it through your SAST/DAST pipeline. We recommend you do.

**Q: If we hold a commercial licence to self-host, does internal use require attribution?**
A: You must keep the licence file conspicuously displayed on each copy or modified copy. Anything beyond that, including end-user-facing credit, is governed by your commercial agreement.

**Q: We want to fork TAOS for our internal needs. Allowed?**
A: You can fork and modify it freely for non-production evaluation and development. Running that fork in production for internal business use requires a commercial licence. Either way the fork must retain this licence on each copy.

**Q: When did the version we are running enter the BSL clock?**
A: Each version's Change Date is the earlier of (a) the explicit Change Date in `LICENSE` and (b) four years after that version was first publicly distributed. Check the LICENSE in the specific commit you are running.

## Contact

For commercial licence enquiries, security questions, DPA requests, or anything else: `angelo.leone1204@gmail.com`.
