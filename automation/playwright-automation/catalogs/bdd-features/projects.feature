Feature: Projects (Operations)
  Nexora page behavior mapped to API /api/v1/workspace/projects; database tables workspace_resources.

  Scenario: NX-BDD-030 Projects: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/workspace/projects and the data tables workspace_resources

  Scenario: NX-BDD-078 Projects: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/workspace/projects and the data tables workspace_resources

  Scenario: NX-BDD-126 Projects: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/workspace/projects and the data tables workspace_resources

  Scenario: NX-BDD-174 Projects: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/workspace/projects and the data tables workspace_resources
