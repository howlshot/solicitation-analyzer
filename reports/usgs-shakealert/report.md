# USGS ShakeAlert Code Review RFI

Generated 2026-10-03 with qwen3.8-27b-mlx. Every item quotes the page it cites.

## Key facts

- **Response due:** October 16, 2026, 12:00 PM (p. 2)
- **Questions due:** Not found
- **Submit:** Submit responses electronically in PDF format via email to the POC. (p. 2)
- **Page limit:** Not found
- **Basis of award:** Not found
- **Set-aside:** Not found
- **NAICS:** Not found

## Deadlines

- [ ] RFI responses are due by October 16, 2026 at 12:00 PM PST. (p. 2)
  > Responses are requested by October 16, 2026 at 12:00pm PST.

## How to submit

- [ ] Submit responses electronically in PDF format via email to the POC. (p. 2)
  > All responses should be submitted electronically in PDF format and emailed
- [ ] Email responses to [name] at [email]. (p. 2)
  > [name] at [email].
- [ ] Include applicable socioeconomic designation in the submission. (p. 2)
  > Applicable socioeconomic designation.
- [ ] Include business size standard in the submission. (p. 2)
  > Business size standard.
- [ ] Include SAM UEI number in the submission. (p. 2)
  > SAM UEI number.
- [ ] Include GSA contract number, if applicable. (p. 2)
  > GSA contract number, if applicable.
- [ ] Include ability to execute all listed tasks. (p. 2)
  > Ability to execute all tasks listed.
- [ ] General marketing information or vendor website references are not responsive. (p. 2)
  > General marketing information or reference to vendor web sites will not be considered responsive
- [ ] Telephone, mail, or fax responses will not be accepted. (p. 2)
  > No telephone, mail, or fax responses will be accepted.
- [ ] All written reports must be submitted in both PDF and editable Word (.docx) format. (Statement of Work, p. 6)
  > All written reports shall be submitted in both PDF and editable Word (.docx) format

## Format and page limits

- [ ] Email subject line must read “RFI: 140G0326Q0223 – ShakeAlert Production System Code Review.” (p. 2)
  > The subject line of the email should read as follows “RFI: 140G0326Q0223 – ShakeAlert Production System Code Review.”

## What the response must include

- [ ] Perform a module-by-module review of source code quality, correctness, and maintainability. (p. 1)
  > A rigorous, module-by-module review of source code quality, correctness, and maintainability.
- [ ] Assess current software development and deployment practices with CI/CD pipeline modernization recommendations. (p. 1)
  > An assessment of current software development and deployment practices, with concrete recommendations for modernizing the CI/CD pipeline
- [ ] Submit capability statements and general approach/solution for listed requirements. (p. 2)
  > Respondents must submit capability statements and information describing the general approach/solution to addressing the listed requirements.
- [ ] Perform deep qualitative review of each module for correctness, reliability, multithreading, and real-time safety. (Statement of Work, p. 3)
  > The contractor shall perform a deep qualitative review of each module, examining:
- [ ] Assess inter-process interactions, message schemas, and handling of ordering and timing dependencies. (Statement of Work, p. 3)
  > Inter-process interactions: correctness of message-passing interfaces (currently ActiveMQ, transitioning to NATS); adherence to defined message schemas
- [ ] Identify all runtime-configurable parameters and document their expected ranges, sensitivity, and default values. (Statement of Work, p. 3)
  > identification of all runtime-configurable parameters in each module; documentation of their expected ranges, sensitivity, and default values
- [ ] Review known issues from prior work and assess whether code-level changes could reduce them. (Statement of Work, p. 3)
  > review of specific issues identified in prior work (e.g., differences in solutions across server instances due to variations
- [ ] Assess data flow and interface consistency across modules for format, units, coordinate systems, and time references. (Statement of Work, p. 3)
  > Data flow and interface consistency: whether module inputs and outputs are consistent in format, units, coordinate systems
- [ ] Review Solution Aggregator logic that merges EPIC, FinDer, and GFAST solutions including edge cases. (Statement of Work, p. 3)
  > specific attention to the Solution Aggregator (SA) logic that merges EPIC, FinDer, and GFAST solutions
- [ ] Review Decision Module logic used to determine if ShakeAlert Message should be published. (Statement of Work, p. 3)
  > review of the Decision Module (DM) logic used to determine if ShakeAlert Message should be published
- [ ] Review alert-pause feature and alert-update thresholds with attention to the 2022 Ferndale earthquake bug case. (Statement of Work, p. 3)
  > review of the alert-pause feature and alert-update thresholds for correctness, with attention to the 2022 Ferndale earthquake bug case
- [ ] Review GitLab repository structure, branching strategy, merge request process, and tagging/versioning practices. (Statement of Work, p. 4)
  > The contractor shall review the current GitLab repository structure, branching strategy, merge request process, and tagging/versioning practices
- [ ] Recommend specific static open-source analysis tools compatible with the ShakeAlert code base. (Statement of Work, p. 4)
  > The contractor shall recommend specific static open-source analysis tools compatible with the ShakeAlert code base
- [ ] Implement at least a baseline CI/CD pipeline configuration in the project’s GitLab repository as Deliverable 6. (Statement of Work, p. 4)
  > The contractor shall implement at least a baseline CI/CD pipeline configuration in the project’s GitLab repository as part of Deliverable 6
- [ ] Review existing coding standards documentation, assess compliance, and recommend a concise, enforceable coding standard. (Statement of Work, p. 4)
  > The contractor shall review the project’s existing coding standards documentation (if any), assess compliance across the code base
- [ ] Review current deployment process and assess reproducibility, rollback capability, configuration management, and deployment testing. (Statement of Work, p. 4)
  > The contractor shall review the current deployment process (Ansible and related tooling) and assess:
- [ ] Review all production modules listed in scope plus modified Earthworm modules and third-party libraries. (Statement of Work, p. 4)
  > The contractor shall review all of the following production modules, plus any Earthworm modules and third-party libraries
- [ ] Review work must be based on the production branch of code at repository access time. (Statement of Work, p. 5)
  > All review work shall be based on the production branch of the code at the time of repository access
- [ ] Contractor must request and document design intent, known limitations, and open issues for each module. (Statement of Work, p. 5)
  > The contractor shall request and document, for each module, the design intent, known limitations, and any open issues
- [ ] Contractor must communicate findings progressively, not only in final reports. (Statement of Work, p. 5)
  > The contractor shall communicate findings to USGS ShakeAlert staff progressively (not only in final reports)
- [ ] Primary recommendations must be technically sound, linked to deficiencies, and actionable within program constraints. (Statement of Work, p. 5)
  > Primary recommendations shall be technically sound, clearly linked to identified deficiencies, and actionable within the constraints
- [ ] Avoid recommendations requiring complete rewrite of major modules unless compelling justification exists. (Statement of Work, p. 5)
  > Recommendations that require a complete rewrite of major modules are unlikely to be actionable and should be avoided
- [ ] Recommendations on inter-process communication must remain valid under anticipated NATS architecture or address both states. (Statement of Work, p. 5)
  > Recommendations related to inter-process communication shall be written to remain valid under the anticipated NATS architecture
- [ ] Apply MISRA C/C++ guidelines or equivalent as reference framework for code review. (Statement of Work, p. 5)
  > MISRA C/C++ guidelines (or equivalent; to be agreed at kickoff based on language profile of code base)
- [ ] Apply CERT C/C++ Secure Coding Standard for security-relevant findings. (Statement of Work, p. 5)
  > CERT C/C++ Secure Coding Standard for security-relevant findings
- [ ] Apply SEI CERT guidelines for concurrency and real-time considerations. (Statement of Work, p. 6)
  > SEI CERT guidelines for concurrency and real-time considerations
- [ ] Apply federal government IT security and software assurance guidance relevant to USGS systems. (Statement of Work, p. 6)
  > Federal government IT security and software assurance guidance relevant to USGS systems
- [ ] Agree on specific standards and tools at kickoff based on languages and build environment. (Statement of Work, p. 6)
  > At kickoff, the contractor and USGS shall agree on the specific standards and tools to be applied
- [ ] Contractor must acknowledge understanding of Intellectual Property rules governing ShakeAlert production code. (Statement of Work, p. 6)
  > The contractor shall acknowledge they understand the Intellectual Property rules which govern the ShakeAlert production code
- [ ] Participate in kickoff meeting within 30 days of contract award. (Statement of Work, p. 6)
  > The contractor shall participate in a kickoff meeting (in person or virtual) within 30 days of contract award
- [ ] Hold at least monthly progress meetings with USGS ShakeAlert technical staff throughout contract period. (Statement of Work, p. 6)
  > The contractor shall hold at least monthly progress meetings with USGS ShakeAlert technical staff throughout the contract period
- [ ] Submit contractor questions in writing or capture them in meeting minutes to create a record. (Statement of Work, p. 6)
  > Contractor questions shall be submitted in writing (e.g. email or issue tracker) or captured in meeting minutes
- [ ] Address USGS comments within 30 days of their review. (Statement of Work, p. 6)
  > the contractor shall address USGS comments within 30 days thereafter
- [ ] Deliver kickoff meeting and work plan in Month 1. (Statement of Work, p. 6)
  > Kickoff meeting and work plan      Month 1                    Meeting + written plan
- [ ] Deliver code metrics baseline report for all modules in Month 3. (Statement of Work, p. 6)
  > Code metrics baseline report       Month 3                    Written report + data files
- [ ] Deliver detailed code review findings for all modules in Month 6. (Statement of Work, p. 6)
  > Detailed code review findings      Month 6                    Written report with prioritized
- [ ] Deliver CI/CD and development practices assessment in Month 8. (Statement of Work, p. 6)
  > CI/CD and development              Month 8                    Written report with
- [ ] Deliver final report and recommendations in Month 11. (Statement of Work, p. 6)
  > Final report and                   Month 11                   Comprehensive report; briefing
- [ ] Demonstrate CI/CD improvements in repository by Month 12. (Statement of Work, p. 6)
  > Demonstration of CI/CD             Month 12                   Working pipeline changes in
- [ ] Conduct kickoff meeting and deliver written work plan within 30 days of award. (Statement of Work, p. 7)
  > Within 30 days of contract award, the contractor shall conduct a kickoff meeting with USGS ShakeAlert technical staff and deliver a written work plan
- [ ] Work plan must specify review methodology, tools, standards, task schedule, POCs, and communication plan. (Statement of Work, p. 7)
  > deliver a written work plan that specifies the review methodology, tools and standards to be applied, task schedule with milestones, points of contact
- [ ] Deliver quantitative code metrics baseline report covering all modules in Section 4. (Statement of Work, p. 7)
  > A quantitative characterization of the code base covering all modules in Section 4. The report shall include per-module and aggregate metrics
- [ ] Metrics report must include LOC, cyclomatic complexity, Halstead metrics, test coverage, and documentation coverage. (Statement of Work, p. 7)
  > The report shall include per-module and aggregate metrics (LOC, cyclomatic complexity, Halstead metrics, test coverage, documentation coverage), a dependency graph
- [ ] Metrics report must include dependency graph and prioritized list of modules flagged for deeper review. (Statement of Work, p. 7)
  > a dependency graph, and a prioritized list of modules and subsystems flagged for deeper review based on the metrics
- [ ] Raw metric data must be provided as machine-readable files (CSV or JSON). (Statement of Work, p. 7)
  > Raw metric data shall be provided as machine-readable files (e.g., CSV or JSON) in addition to the narrative report
- [ ] Deliver module-by-module code review report organized by Section 3.1.2 review dimensions. (Statement of Work, p. 7)
  > A module-by-module code review report organized by the review dimensions in Section 3.1.2
- [ ] Each finding must identify affected module/file, describe issue/impact, assign severity rating, and provide recommendation. (Statement of Work, p. 7)
  > For each finding, the report shall identify the affected module and file, describe the issue and its potential impact on alert reliability or correctness
- [ ] Findings must include consolidated findings table for prioritization. (Statement of Work, p. 7)
  > The report shall include a consolidated findings table for easy prioritization
- [ ] Critical and High severity findings must include proposed code changes where practical. (Statement of Work, p. 7)
  > Critical and High severity findings shall include proposed code changes (pseudocode or actual code) where practical
- [ ] Deliver CI/CD and development practices assessment report covering GitLab workflow, static analysis, coding standards, deployment. (Statement of Work, p. 7)
  > A report covering the assessment of GitLab workflow, automated static analysis tooling, coding standards, and deployment practices described in Section 3.2
- [ ] CI/CD assessment must describe current practice, identify gaps, and provide prioritized recommendations with effort estimates. (Statement of Work, p. 7)
  > For each area, the report shall describe current practice, identify gaps relative to applicable standards and industry practice, and provide prioritized
- [ ] CI/CD assessment must include step-by-step implementation guide for recommended pipeline improvements. (Statement of Work, p. 7)
  > The report shall include a step-by-step implementation guide for the recommended CI/CD pipeline improvements
- [ ] Deliver comprehensive final report synthesizing findings with prioritized action plan and executive summary. (Statement of Work, p. 7)
  > A comprehensive final report that synthesizes findings across all tasks, highlights the most impactful improvements, and provides a recommended prioritized action plan
- [ ] Final report must include executive summary suitable for non-technical stakeholders. (Statement of Work, p. 7)
  > The report shall include an executive summary suitable for non-technical stakeholders
- [ ] Present findings to ShakeAlert staff and program management in virtual briefing of approximately two hours. (Statement of Work, p. 7)
  > The contractor shall present the findings to ShakeAlert technical staff and program management in a virtual briefing of approximately two hours
- [ ] Implement working CI/CD configuration changes in ShakeAlert GitLab repository, reviewed and approved by USGS. (Statement of Work, p. 7)
  > Working CI/CD configuration changes implemented in the ShakeAlert GitLab repository, reviewed and approved by USGS
- [ ] CI/CD pipeline must automate build verification, static analysis, unit test execution, and coverage reporting on every merge request. (Statement of Work, p. 7)
  > that automate at a minimum: build verification, static analysis (linting and complexity checks), unit test execution, and coverage reporting on every merge request
- [ ] Document pipeline configuration and provide brief user guide for ShakeAlert staff. (Statement of Work, p. 7)
  > The contractor shall document the pipeline configuration and provide a brief user guide for ShakeAlert staff
- [ ] Period of performance is 12 months from date of contract award. (Statement of Work, p. 8)
  > Period of performance: 12 months from date of contract award
- [ ] All work may be performed remotely; travel to USGS facilities is not required. (Statement of Work, p. 8)
  > All work may be performed remotely. Travel to USGS facilities is not required but may be proposed by the contractor
- [ ] Treat all non-public ShakeAlert code, configuration, and documentation as sensitive; do not disclose to third parties. (Statement of Work, p. 8)
  > The contractor shall treat all non-public ShakeAlert code, configuration, and documentation as sensitive and shall not disclose it to third parties
- [ ] NDA or comparable instrument will be executed at contract award. (Statement of Work, p. 8)
  > A non-disclosure agreement (NDA) or comparable instrument will be executed at contract award
- [ ] Contractor is not expected to implement code fixes; that responsibility remains with USGS staff. (Statement of Work, p. 8)
  > The contractor is not expected to implement code fixes; that responsibility remains with USGS staff
- [ ] Exception: contractor will implement CI/CD pipeline changes in repository under USGS review (Deliverable 6). (Statement of Work, p. 8)
  > The exception is Deliverable 6, where the contractor will implement CI/CD pipeline changes in the repository under USGS review
- [ ] All recommendations shall consider USGS strong preference to use open-source code, libraries, and tools. (Statement of Work, p. 8)
  > All recommendations shall consider the strong preference of USGS to use open-source code, libraries, and tools
- [ ] Contractor personnel performing code review shall have demonstrated experience in real-time or safety-critical software systems. (Statement of Work, p. 8)
  > Contractor personnel performing the code review shall have demonstrated experience in real-time or safety-critical software systems
- [ ] Relevant domain experience in seismology or geophysical data processing is desirable but not required. (Statement of Work, p. 8)
  > Relevant domain experience in seismology or geophysical data processing is desirable but not required
