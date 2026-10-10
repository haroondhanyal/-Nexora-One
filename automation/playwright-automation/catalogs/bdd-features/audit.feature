Feature: Audit history (Governance)
  Nexora page behavior mapped to API /api/v1/audit; database tables audit_events.

  Scenario: NX-BDD-006 Audit history: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/audit and the data tables audit_events

  Scenario: NX-BDD-054 Audit history: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/audit and the data tables audit_events

  Scenario: NX-BDD-102 Audit history: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/audit and the data tables audit_events

  Scenario: NX-BDD-150 Audit history: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/audit and the data tables audit_events

  Scenario: NX-BDD-198 Audit history: the owner changes to another workspace
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner changes to another workspace
    Then only data belonging to the selected workspace is shown
    And the result is consistent with the screen API /api/v1/audit and the data tables audit_events
