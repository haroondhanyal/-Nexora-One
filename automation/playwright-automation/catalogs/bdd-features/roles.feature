Feature: Roles & permissions (Governance)
  Nexora page behavior mapped to API /api/v1/roles; Application RBAC policy configuration.

  Scenario: NX-BDD-005 Roles & permissions: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/roles and the configured identity/session state

  Scenario: NX-BDD-053 Roles & permissions: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/roles and the configured identity/session state

  Scenario: NX-BDD-101 Roles & permissions: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/roles and the configured identity/session state

  Scenario: NX-BDD-149 Roles & permissions: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/roles and the configured identity/session state

  Scenario: NX-BDD-197 Roles & permissions: the owner changes to another workspace
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner changes to another workspace
    Then only data belonging to the selected workspace is shown
    And the result is consistent with the screen API /api/v1/roles and the configured identity/session state
