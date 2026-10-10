Feature: Branches (Workspace)
  Nexora page behavior mapped to API /api/v1/branches; database tables branches.

  Scenario: NX-BDD-004 Branches: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/branches and the data tables branches

  Scenario: NX-BDD-052 Branches: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/branches and the data tables branches

  Scenario: NX-BDD-100 Branches: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/branches and the data tables branches

  Scenario: NX-BDD-148 Branches: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/branches and the data tables branches

  Scenario: NX-BDD-196 Branches: the owner changes to another workspace
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner changes to another workspace
    Then only data belonging to the selected workspace is shown
    And the result is consistent with the screen API /api/v1/branches and the data tables branches
