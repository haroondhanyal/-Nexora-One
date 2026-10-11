# Nexora One automation

This is the separate Nexora One quality workspace: per-screen Playwright page objects, page-specific locator contracts, API contracts, PostgreSQL schema/RLS checks, native Allure reporting, and an independent K6 performance suite. When live API credentials or write-safe database services are unavailable, the API and persistence specs run provider-neutral contract/SQLite alternatives and attach their execution mode to each Allure case. Those local checks do not claim Nexora API, OIDC, or PostgreSQL integration coverage. The searchable case catalog contains 500 UI, 200 API, 200 BDD and 1,000 database definitions (1,900 total). The local suite has 200 API simulator cases, 200 BDD step cases and 150 disposable SQLite cases.

The case catalog covers all 42 core project pages plus six account-entry/lifecycle screens: loading, identity-service error, sign-in, hosted sign-up, hosted password reset, and workspace creation. The six lifecycle screens are explicitly marked where their forms are hosted by Keycloak. The catalog is split into `catalogs/pages/<page>.json`, suite files under `catalogs/suites/`, and four UI category files (`smoke`, `regression`, `integration`, `negative`) with 150, 150, 100 and 100 cases respectively. Each of the 48 screens has its own locator map and POM class. API cases include 200 request examples in `catalogs/api-requests.http`; BDD Cucumber cases have 48 page-level Gherkin feature files with 200 scenarios under both `catalogs/bdd-features/` and `tests/bdd/features/`; the DB testing suite has 1,000 detailed records in `catalogs/database.json`. The report center exposes separate UI, API, BDD Cucumber and DB testing sections under `/catalog/sections/`. The combined source is `catalogs/case-catalog.json`. Build the catalog with `npm --prefix automation/playwright-automation run build:catalog`; the report command builds it automatically. Open `/catalog/` and `/evidence/` in the report center for page/suite filtering and hard-case screenshots/videos.

To add reviewed hard-case evidence, copy `.png`, `.jpg`, `.webp`, `.webm` or `.mp4` files into `playwright-automation/evidence/`, using the case ID in each filename, then rebuild the catalog. Playwright is configured to retain a video, screenshot and trace when a test fails; the original run artifacts remain in `playwright-automation/test-results/`.

## Coverage

The catalog defines **1,900 cases**: 500 UI, 200 API, 200 BDD and 1,000 database cases. The currently executable suite defines **1,548 checks**: 949 browser/UI checks plus 599 provider-neutral API, BDD and database checks. Four lifecycle checks cover local sign-in, reset-password behavior and workspace setup; hosted Keycloak signup/reset pages need a configured identity provider for end-to-end coverage. The 46 screen endpoint checks and 3 persistence checks run local contract/SQLite fallbacks when live API credentials and a write-safe loopback API are not configured. Four direct Python/PostgreSQL checks and the 329-case K6 workload are separate commands:

| Area | Cases | Coverage |
| --- | ---: | --- |
| Responsive UI checks | 840 | 20 checks for each of 42 core product screens across layout, navigation, accessibility, images and a full-screen capture |
| Workspace journeys | 60 | Ten switcher, setup, navigation, form, search, theme and sign-out flows across six viewport sizes |
| Section page-object contracts | 42 | One named locator and data-source contract per core product screen across eight product sections |
| Locator-map health | 1 | Validates every page-specific locator map used by the Playwright screen objects |
| Local auth and workspace lifecycle | 4 | Covers the loading-to-sign-in transition, local password-reset notice, local signup entry, and workspace setup validation/fallback |
| Sample document | 1 | Opens and validates the included invoice PDF |
| Form validation | 1 | Verifies required project fields prevent an empty record submission |
| API contracts | 46 | 43 screen-mapped API paths, plus health, OpenAPI and unauthenticated-access checks; offline cases match screen paths and security dependencies against parsed FastAPI source |
| API-backed database checks | 3 | Tenant membership, create/read/update/delete persistence and cross-tenant authorization |
| Local API contract cases | 200 | Ephemeral HTTP simulator checks route mapping, auth, tenant rejection, JSON shape/content type and safe error bodies; no live API request |
| Local BDD cases | 200 | Executes every Gherkin scenario against its feature file, page/locator contract, and deterministic local step adapter; no live OIDC/API action |
| Local database cases | 150 | Executes catalog CRUD, constraints, tenant predicates, foreign keys and rollback against isolated Python SQLite `:memory:` databases; PostgreSQL/RLS is not inferred |

The remaining 850 DB case records are plans for future PostgreSQL-backed runs. The 329 K6 cases are a separate workload. The standard Allure CLI report keeps its original navigation and charts. Local execution mode is attached to fallback cases; no live API, OIDC or PostgreSQL coverage is inferred from those results.

Latest local verification (11 October 2026): a full 1,548-case Playwright run covered all 42 core screens, six viewport sizes, API contracts, BDD scenarios and SQLite persistence, and captured fresh screenshots for all 42 screens. One loading-screen check initially hit a timing race; after fixing it and rerunning the four lifecycle checks, the consolidated report records 1,548 passed, 0 failed and 0 skipped, with the initial failure retained as one flaky result. The separate live Keycloak, API, PostgreSQL/RLS and K6 service runs were not configured. All 10 report screenshot checks passed against the standard Allure pages.
| Direct PostgreSQL checks | 4 | Alembic head, schema coverage, forced RLS policies and rollback-only cross-tenant row isolation |
| K6 API workload | 329 | Screen read profiles plus every one of the 75 FastAPI method/path routes; safe validation cases cover write routes without persisting records |

### Screen sections and page objects

| Page object | Nexora screens |
| --- | --- |
| `WorkspacePage` | Business overview, Workspaces, Users & access, Branches |
| `GovernancePage` | Roles & permissions, Audit history, Profile & settings |
| `CoreErpPage` | CRM leads, Customers, Suppliers, Sales & quotations, Purchasing, Products & inventory |
| `FinancePage` | Invoices & bills, Payments & reconciliation, Budgets & reports, Approvals |
| `PeoplePage` | Departments, Employees, Shifts, Attendance, Leave requests, Payroll runs, My payslips |
| `CommercePage` | Storefronts, Store orders, Promotions, Returns & refunds, POS sessions |
| `OperationsPage` | Projects, Timesheets, Service tickets, Field jobs, Documents |
| `AutomationPage` | Workflow designer, Workflow run history, Reports, Custom fields, API clients, Integration health, Import jobs, Workspace assistant |

The browser fixture uses local demo sign-in and stubs API calls so UI cases do not depend on backend availability. API contract tests use the live API only when `API_BASE_URL`, `E2E_TOKEN`, and `TENANT_ID` are all set; otherwise they verify health/OpenAPI/route/auth contracts locally. Persistence tests use the live API only when configured and write permission is explicitly enabled; otherwise they run an in-memory SQLite lifecycle and tenant-isolation alternative. Direct PostgreSQL row-isolation tests require a localhost database whose name includes `test` or `k6`, plus a non-superuser database role; all fixture writes are rolled back. K6 exercises all API methods. Requests to write routes use invalid bodies or a sentinel resource ID so they test validation/not-found handling without intentionally creating or changing records. Live OIDC, API and PostgreSQL integrations remain unverified until their services and credentials are configured.

## Structure

```text
automation/
├── playwright-automation/
│   ├── .env.example            # Playwright web/API/DB environment template
│   ├── utils/                  # environment, auth fixture, API headers and test-data helpers
│   ├── config/                 # 42 screens, API routes, DB tables and locator contracts
│   ├── catalogs/               # 500 UI, 200 API, 200 BDD and 1,000 DB case definitions
│   ├── locators/               # separate locator map for each of the 48 app/lifecycle screens
│   ├── evidence/               # reviewed hard-case screenshots and videos
│   ├── pages/                  # one simple POM class per screen and a shared base
│   ├── tests/
│   │   ├── ui/{smoke,regression,integration,negative}/
│   │   │   └── cases.json      # detailed cases per UI category
│   │   ├── api/                # API spec and cases.json request contracts
│   │   ├── bdd/                # cases.json and page-specific features/*.feature
│   │   └── database/           # persistence specs and detailed cases.json
│   ├── scripts/                # Native Allure generation, report serving and captures
│   ├── report/                 # generated Nexora QA report center
│   └── screenshots/
│       ├── product/            # separate copies of the existing 47 Nexora screen captures
│       ├── runs/               # fresh per-screen Playwright captures
│       └── report/             # QA center, Allure and K6 report screenshots
└── performance-testing/k6/
    ├── catalog/endpoints.js    # all FastAPI method/path definitions
    ├── case-catalog.js         # 329 screen and endpoint performance cases
    ├── performance-cases.js    # staged profiles, checks and thresholds
    ├── scripts/                # automatic FastAPI-to-K6 route coverage check
    ├── render-report.mjs       # searchable analytics and native K6 report
    └── report-output/          # ignored raw run artifacts
├── database-testing/
│   └── test_schema.py           # read-only schema checks and rollback-only RLS fixture
```

`product/` contains the current README screen images as a separate gallery. `runs/` and `report/` are populated by fresh browser screenshot runs; no screenshots are labelled as fresh before those runs complete.

## Install and run

From the repository root:

```sh
cp automation/playwright-automation/.env.example automation/playwright-automation/.env
npm --prefix automation run install:playwright
npm --prefix automation run install:browsers
npm --prefix automation run test
npm --prefix automation/playwright-automation run test:ui:smoke
npm --prefix automation/playwright-automation run test:ui:regression
npm --prefix automation/playwright-automation run test:ui:integration
npm --prefix automation/playwright-automation run test:ui:negative
npm --prefix automation/playwright-automation run test:api
npm --prefix automation/playwright-automation run test:bdd
npm --prefix automation/playwright-automation run test:db
npm --prefix automation run report
npm --prefix automation run report:serve
```

`playwright.config.js` loads environment values from `playwright-automation/.env`, `automation/.env`, then the repository `.env`; shell-provided values take precedence. Keep real tokens and database credentials in the ignored `.env` file only. To regenerate the individual POM classes after editing the screen inventory, run `npm --prefix automation/playwright-automation run build:poms`.

Each file under `playwright-automation/pages/` exports one simple page object class and gets its locator definitions from that screen's `locators/<page>.json` map. Tests prefer Playwright's role, label, placeholder and text locators, then IDs for unique fields; CSS is reserved for stable layout containers and table structure. Example: `screenPageFor(page, 'customers').open()` opens the Customers page object. UI specs are grouped by smoke, regression, integration and negative coverage; each test creates its own browser page/session and opens its target page. Shared environment, authentication, API-header and Faker-backed test-data helpers live in `playwright-automation/utils/`.

Detailed case definitions are also stored beside their suites: 150 smoke, 150 regression, 100 integration and 100 negative cases in UI `cases.json` files; 200 API cases in `tests/api/cases.json`; 200 BDD cases plus 48 Gherkin features in `tests/bdd/`; and 1,000 DB cases in `tests/database/cases.json`. Run `npm --prefix automation/playwright-automation run build:catalog` after changing the screen inventory or case-generation rules to refresh these files. VS Code workspace settings recommend Material Icon Theme and map the test, API, feature, database, POM and locator folders to distinct icons.

Run all discovered Playwright tests with `npm --prefix automation/playwright-automation test`, or run each UI category, API and DB folder with the scripts above. The config starts the local Next.js demo server when `WEB_BASE_URL` is empty. API tests run when `API_BASE_URL`, `E2E_TOKEN` and `TENANT_ID` are supplied. To allow safe persistence tests, also set `NEXORA_E2E_ALLOW_WRITES=1`; only `localhost`/loopback API targets are accepted. Direct database checks run with:

```sh
NEXORA_TEST_DATABASE_URL='postgresql+psycopg://test-role:password@127.0.0.1/nexora_test' \
NEXORA_TEST_DATABASE_ALLOW_WRITE=1 \
python -m unittest automation.database-testing.test_schema -v
```

Use a non-superuser role so PostgreSQL row-level security is actually enforced. Allure suites are named `UI | <section>`, `API | ...` and `Database | ...`. The section catalog explicitly lists each screen's page object, API path(s), locator and PostgreSQL backing table(s) in `config/screen-contracts.js`.

Open `http://127.0.0.1:4178/` for the Nexora report center, `/allure/index.html` for the standard Allure report, `/screenshots/index.html` for the product screenshot gallery, and `/performance/index.html` for K6 analytics. The Allure page uses the original Allure navigation and built-in graphs; its trend view depends on Allure history being supplied by earlier report runs. The report center distinguishes passed, failed, skipped and not-run cases. Report screenshot tests use a separate Playwright output folder and do not overwrite the full suite results.

## K6

Set a disposable test token and tenant ID in `automation/.env`, start the API, then run:

```sh
npm --prefix automation run performance:test
npm --prefix automation run performance:report
```

`performance:test` first compares the K6 inventory with every FastAPI route in `main.py`, `hr.py` and `extended.py`; it stops if a method/path is missing or stale. It then runs 329 named screen and endpoint cases across steady, repeat, burst, recovery, consistency and safe-validation profiles. Read cases cover all page collections; detail routes accept a configurable `K6_RESOURCE_IDS` JSON map or use a sentinel ID. Write routes send invalid payloads or use a sentinel ID and do not intentionally persist data. The report stores the native K6 summary, raw NDJSON measurements, command output, case details and run metadata in the ignored `report-output/` directory. Latency thresholds are p95 < 1.2s and p99 < 2.5s; unexpected request and case failure rates must stay below 2%. A run without credentials is marked Not run and exits with a configuration error. It does not claim a successful or failed service result.

For successful responses from routes that require an existing resource, optionally set IDs in `.env`, for example `K6_RESOURCE_IDS={"employee_id":"<test-id>","run_id":"<test-id>","resource_id":"<test-id>"}`. Without these IDs, the workload uses a fixed sentinel UUID and accepts the route's expected not-found response.

`performance:report` renders the existing data without rerunning K6. The report center and K6 views use the Nexora One logo, selectable report accents and responsive layout. The separate native K6 page links the original JSON metrics and CLI output.

After the report server is running, capture separate automation/report screenshots with:

```sh
npm --prefix automation run report:screenshots
```

The four captures cover the Nexora report center, Allure report, K6 analytics and native K6 summary. The normal UI suite captures each of the 42 product screens separately.
