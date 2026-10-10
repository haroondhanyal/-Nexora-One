Feature: Sign up (Authentication)
  Nexora page behavior mapped to Keycloak hosted account-registration flow.

  Scenario: NX-BDD-046 Sign up: a visitor submits valid registration details
    Given a visitor is on the Nexora account lifecycle
    When a visitor submits valid registration details
    Then the identity provider accepts the details or displays its configured verification step
    And the result is consistent with Keycloak hosted account-registration flow and the configured Keycloak identity provider

  Scenario: NX-BDD-094 Sign up: a visitor submits invalid registration details
    Given a visitor is on the Nexora account lifecycle
    When a visitor submits invalid registration details
    Then field-level validation is shown and no account is created
    And the result is consistent with Keycloak hosted account-registration flow and the configured Keycloak identity provider

  Scenario: NX-BDD-142 Sign up: a visitor uses an email already registered
    Given a visitor is on the Nexora account lifecycle
    When a visitor uses an email already registered
    Then the provider displays its safe duplicate-account response
    And the result is consistent with Keycloak hosted account-registration flow and the configured Keycloak identity provider

  Scenario: NX-BDD-190 Sign up: a visitor submits mismatched password confirmation
    Given a visitor is on the Nexora account lifecycle
    When a visitor submits mismatched password confirmation
    Then password confirmation validation prevents submission
    And the result is consistent with Keycloak hosted account-registration flow and the configured Keycloak identity provider
