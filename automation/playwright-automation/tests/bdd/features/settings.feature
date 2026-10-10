Feature: Profile & settings (Governance)
  Nexora page behavior mapped to API /api/v1/company-profile, /api/v1/me/preferences; database tables tenants, user_preferences.

  Scenario: NX-BDD-007 Profile & settings: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/company-profile, /api/v1/me/preferences and the data tables tenants, user_preferences

  Scenario: NX-BDD-055 Profile & settings: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/company-profile, /api/v1/me/preferences and the data tables tenants, user_preferences

  Scenario: NX-BDD-103 Profile & settings: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/company-profile, /api/v1/me/preferences and the data tables tenants, user_preferences

  Scenario: NX-BDD-151 Profile & settings: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/company-profile, /api/v1/me/preferences and the data tables tenants, user_preferences

  Scenario: NX-BDD-199 Profile & settings: the owner changes to another workspace
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner changes to another workspace
    Then only data belonging to the selected workspace is shown
    And the result is consistent with the screen API /api/v1/company-profile, /api/v1/me/preferences and the data tables tenants, user_preferences
