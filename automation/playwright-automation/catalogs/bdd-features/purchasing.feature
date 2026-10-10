Feature: Purchasing (Core ERP)
  Nexora page behavior mapped to API /api/v1/records/purchasing; database tables business_records.

  Scenario: NX-BDD-012 Purchasing: an owner opens the page
    Given the Nexora owner is authenticated or is creating a workspace
    When an owner opens the page
    Then the page heading and primary content are visible
    And the result is consistent with the screen API /api/v1/records/purchasing and the data tables business_records

  Scenario: NX-BDD-060 Purchasing: the owner searches for a known record
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner searches for a known record
    Then the matching record is shown and unrelated records are hidden
    And the result is consistent with the screen API /api/v1/records/purchasing and the data tables business_records

  Scenario: NX-BDD-108 Purchasing: the owner submits valid required fields
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner submits valid required fields
    Then the record is saved and displayed in the active workspace
    And the result is consistent with the screen API /api/v1/records/purchasing and the data tables business_records

  Scenario: NX-BDD-156 Purchasing: the owner omits a required field
    Given the Nexora owner is authenticated or is creating a workspace
    When the owner omits a required field
    Then field validation appears and the record is not saved
    And the result is consistent with the screen API /api/v1/records/purchasing and the data tables business_records
