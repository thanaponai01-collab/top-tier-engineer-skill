# Optional CI setup

Read the installed verify-loop references/ci.md and assets/verify.yml as the authoritative runner
contract and template. Keep the runner unchanged; adapt project inputs and environment.

1. Identify the existing CI provider, Git project path, runtime, package manager and dependencies.
   Reuse existing jobs. The bundled template is GitHub Actions; another provider needs equivalent
   execution and artifact steps rather than copied YAML.
2. Complete the recipe and spec-backed mutations. The committed repo-relative plan names exact
   features and mutation files. Strict proof needs rejection evidence for every mapped feature.
3. Pin a reviewed verifier commit supporting ci and confirm that command exists at the pin.
   Provision Python 3.12+ and Git alongside the native project runtime. Use disposable services
   without production credentials; report missing prerequisites.
4. CI archives only the selected committed directory: no .git, ignored dependencies or parent
   files. Install dependencies in scratch through recipe setup as needed. Installing node_modules
   only in the checkout does not populate the archive. Shared monorepo inputs may require the Git
   root plus package-qualified commands. History-dependent checks need an adapted harness or
   explicit blocked status.
5. Preserve read-only permissions, disabled persisted checkout credentials, pinned verifier source
   and artifact upload on failure. Write evidence outside the entire Git checkout. Record the
   actual tested commit, provider event semantics and retention; redact sensitive output.
6. Validate from a clean committed checkout. If commits/pushes are outside authorization, leave
   concrete configuration reviewable and report hosted validation pending. When authorized,
   observe the real hosted run and inspect report/state/log before declaring CI verified.

Green binds selected inputs and expectations; review protects candidate-authored proof and pins.
Fresh execution alone does not establish independent oracle ownership. CI setup adds no deployment.
Build/review/release skills can consume evidence independently, without requiring setup first.
