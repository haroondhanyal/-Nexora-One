Feature: Workspaces (Workspace)
  Nexora page behavior mapped to API /api/v1/me/workspaces; database tables tenants, memberships.

  Scenario: NX-BDD-002 Workspaces: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/me/workspaces and the data tables tenants, memberships

  Scenario: NX-BDD-050 Workspaces: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/me/workspaces and the data tables tenants, memberships

  Scenario: NX-BDD-098 Workspaces: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/me/workspaces and the data tables tenants, memberships

  Scenario: NX-BDD-146 Workspaces: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/me/workspaces and the data tables tenants, memberships

  Scenario: NX-BDD-194 Workspaces: the owner changes to another workspace
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner changes to another workspace
    Then only data belonging to the selected workspace is shown
    And the result is consistent with the screen API /api/v1/me/workspaces and the data tables tenants, memberships
