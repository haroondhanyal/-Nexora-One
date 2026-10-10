Feature: Payroll runs (People)
  Nexora page behavior mapped to API /api/v1/hr/payroll/runs; database tables payroll_runs.

  Scenario: NX-BDD-023 Payroll runs: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/hr/payroll/runs and the data tables payroll_runs

  Scenario: NX-BDD-071 Payroll runs: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/hr/payroll/runs and the data tables payroll_runs

  Scenario: NX-BDD-119 Payroll runs: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/hr/payroll/runs and the data tables payroll_runs

  Scenario: NX-BDD-167 Payroll runs: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/hr/payroll/runs and the data tables payroll_runs
