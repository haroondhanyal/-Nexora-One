Feature: Forgot/reset password (Authentication)
  Nexora page behavior mapped to Keycloak hosted forgot-credentials flow.

  Scenario: NX-BDD-047 Forgot/reset password: a user submits a registered email
    Given a visitor is on the Nexora account lifecycle
    When a user submits a registered email
    Then the identity provider displays its configured reset confirmation without revealing account existence
    And the result is consistent with Keycloak hosted forgot-credentials flow and the configured Keycloak identity provider

  Scenario: NX-BDD-095 Forgot/reset password: a user submits an invalid email
    Given a visitor is on the Nexora account lifecycle
    When a user submits an invalid email
    Then the email field validation is displayed
    And the result is consistent with Keycloak hosted forgot-credentials flow and the configured Keycloak identity provider

  Scenario: NX-BDD-143 Forgot/reset password: a user submits an unregistered email
    Given a visitor is on the Nexora account lifecycle
    When a user submits an unregistered email
    Then the same safe confirmation is shown without account enumeration
    And the result is consistent with Keycloak hosted forgot-credentials flow and the configured Keycloak identity provider

  Scenario: NX-BDD-191 Forgot/reset password: a user opens an expired reset link
    Given a visitor is on the Nexora account lifecycle
    When a user opens an expired reset link
    Then the provider offers a safe retry path without changing the password
    And the result is consistent with Keycloak hosted forgot-credentials flow and the configured Keycloak identity provider
