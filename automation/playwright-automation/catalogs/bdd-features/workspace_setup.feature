Feature: Create workspace (Workspace setup)
  Nexora page behavior mapped to database tables tenants, memberships.

  Scenario: NX-BDD-048 Create workspace: the owner submits a valid company name and industry
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits a valid company name and industry
    Then one workspace and its initial owner membership are created
    And the result is consistent with PostgreSQL: tenants, memberships and the data tables tenants, memberships

  Scenario: NX-BDD-096 Create workspace: the owner submits an empty company name
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits an empty company name
    Then required-field validation appears and no workspace is created
    And the result is consistent with PostgreSQL: tenants, memberships and the data tables tenants, memberships

  Scenario: NX-BDD-144 Create workspace: the owner selects a different industry
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner selects a different industry
    Then the selected industry is shown as the active choice before submission
    And the result is consistent with PostgreSQL: tenants, memberships and the data tables tenants, memberships

  Scenario: NX-BDD-192 Create workspace: the owner submits a company name below the minimum length
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits a company name below the minimum length
    Then validation appears and no tenant is created
    And the result is consistent with PostgreSQL: tenants, memberships and the data tables tenants, memberships
