Feature: Service tickets (Operations)
  Nexora page behavior mapped to API /api/v1/workspace/service_tickets; database tables workspace_resources.

  Scenario: NX-BDD-032 Service tickets: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/workspace/service_tickets and the data tables workspace_resources

  Scenario: NX-BDD-080 Service tickets: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/workspace/service_tickets and the data tables workspace_resources

  Scenario: NX-BDD-128 Service tickets: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/workspace/service_tickets and the data tables workspace_resources

  Scenario: NX-BDD-176 Service tickets: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/workspace/service_tickets and the data tables workspace_resources
